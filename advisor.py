import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODELS = ["gemini-flash-latest"]
LAST_MODEL = PRIMARY_MODEL   # the model that actually answered last


def _client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("API key not found. Add GEMINI_API_KEY to your .env file.")
    return genai.Client(api_key=key)


def _generate(contents, system=None):
    global LAST_MODEL
    client = _client()
    last_error = None
    for model in [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]:
        try:
            config = {"system_instruction": system} if system else None
            response = client.models.generate_content(model=model, contents=contents, config=config)
            LAST_MODEL = model
            return response.text
        except Exception as e:
            last_error = e
            if "404" in str(e) or "NOT_FOUND" in str(e):
                continue          # model unavailable, try the next one
            raise
    raise last_error


def list_models():
    names = [m.name.replace("models/", "") for m in _client().models.list() if "gemini" in m.name]
    return sorted(names)


def build_context(analysis, details):
    if not analysis:
        return "The student has not entered any marks yet."
    lines = [f"- {n}: {r['marks']:g}/{r['total']:g} ({r['percentage']}%), grade {r['grade']}, "
             f"{r['credits']:g} credit hours" for n, r in analysis["subjects"].items()]
    scale = ", ".join(f"{s['grade']} >= {s['min']:g}% ({s['points']:g} pts)" for s in analysis["scale"])
    extra = []
    if details.get("study_hours"):
        extra.append(f"Study hours per week: {details['study_hours']}")
    if details.get("absences"):
        extra.append(f"Absences this term: {details['absences']}")
    if details.get("goal"):
        extra.append(f"Student's goal: {details['goal']}")
    if details.get("predicted") is not None:
        extra.append(f"ML model predicts a final result of about {details['predicted']}% if nothing changes")
    return (
        "Student results:\n" + "\n".join(lines) + "\n\n"
        f"Overall: {analysis['overall_percentage']}% (grade {analysis['overall_grade']}), "
        f"credit-weighted GPA {analysis['overall_gpa']} out of {analysis['max_points']:g}\n"
        f"Pass mark: {analysis['pass_mark']:g}%\n"
        f"Weakest subject: {analysis['weakest']}; strongest: {analysis['strongest']}\n"
        f"Grading system used: {scale}\n" + "\n".join(extra)
    )


def get_advice(analysis, details):
    prompt = f"""You are a friendly academic advisor.

{build_context(analysis, details)}

Write a short, practical improvement plan with these sections:
1. Quick assessment (2 sentences)
2. Priority subjects and why (consider credit hours: high-credit weak subjects matter most for GPA)
3. A weekly study plan (specific, realistic)
4. Three concrete study techniques for the weakest subject
5. One encouraging closing line
Keep it under 350 words. Use simple language."""
    try:
        return _generate(prompt)
    except Exception as e:
        return f"Could not get AI advice right now ({e}). Your grades above are still correct."


def chat_reply(history, analysis, details):
    """history = [{'role': 'user' | 'assistant', 'content': str}, ...] ending with the user's message."""
    system = (
        "You are a friendly, concise academic advisor chatbot inside a student grade app. "
        "Answer using the student's data below. Do not invent marks or facts. "
        "Give practical study advice, explain grades and GPA, and help with what-if questions. "
        "If a question is unrelated to studies, politely steer back.\n\n"
        + build_context(analysis, details)
    )
    contents = [{"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]} for m in history[-12:]]
    try:
        return _generate(contents, system=system)
    except Exception as e:
        return f"Sorry, I could not answer right now ({e})."