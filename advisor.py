import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = "gemini-2.5-flash"  # if you get a model error, check AI Studio for the current name


def build_prompt(analysis, study_hours=None, absences=None, goal=None, predicted=None):
    lines = []
    for name, r in analysis["subjects"].items():
        lines.append(f"- {name}: {r['marks']}/{r['total']} ({r['percentage']}%), grade {r['grade']}")

    extra = []
    if study_hours is not None:
        extra.append(f"Study hours per week: {study_hours}")
    if absences is not None:
        extra.append(f"Absences this term: {absences}")
    if goal:
        extra.append(f"Student's goal: {goal}")
    if predicted is not None:
        extra.append(f"ML model predicts the final result will be about {predicted}% if nothing changes")

    return f"""You are a friendly academic advisor. A student has these results:

{chr(10).join(lines)}

Overall: {analysis['overall_percentage']}%, GPA {analysis['overall_gpa']}/4.0
Weakest subject: {analysis['weakest']}
Strongest subject: {analysis['strongest']}
{chr(10).join(extra)}

Give a short, practical improvement plan with these sections:
1. Quick assessment (2 sentences)
2. Priority subjects and why
3. A weekly study plan (specific, realistic)
4. Three concrete study techniques for the weakest subject
5. One encouraging closing line
Keep it under 350 words. Use simple language."""


def get_advice(analysis, study_hours=None, absences=None, goal=None, predicted=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ API key not found. Add GEMINI_API_KEY to your .env file."
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=build_prompt(analysis, study_hours, absences, goal, predicted),
        )
        return response.text
    except Exception as e:
        return f"⚠️ Could not get AI advice right now ({e}). Your grades above are still correct."