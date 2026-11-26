import html

import altair as alt
import pandas as pd
import streamlit as st

import advisor
from grading import DEFAULT_PRESET, PRESETS, analyze, clean_scale
from predictor import predict_final

st.set_page_config(page_title="Student Grade Advisor", page_icon=":material/school:", layout="wide")

PALETTE = ["#0F766E", "#15803D", "#65A30D", "#CA8A04", "#EA580C", "#DC2626"]  # best -> worst

ICONS = {
    "percent": '<line x1="19" x2="5" y1="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
    "award": '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
    "chart": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" x2="4" y1="22" y2="15"/>',
    "cap": '<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/><path d="M22 10v6"/>',
    "trend": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
}


def svg(name, size=22, color="currentColor"):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


st.markdown("""
<style>
footer, #MainMenu {visibility: hidden;}
.block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1150px;}
.hero {background: #0B2A3C; border-radius: 14px; padding: 1.6rem 2rem; color: #fff; margin-bottom: 1.2rem;
       display: flex; align-items: center; gap: 1.1rem;}
.hero-icon {background: #0F766E; border-radius: 12px; padding: .75rem; display: flex;}
.hero h1 {margin: 0; font-size: 1.7rem; font-weight: 700; color: #fff; padding: 0;}
.hero p {margin: .25rem 0 0 0; color: #B6C8D4; font-size: .98rem;}
.stat-card {background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem 1.1rem;
            display: flex; gap: .9rem; align-items: center; height: 100%;}
.stat-icon {border-radius: 10px; padding: .6rem; display: flex;}
.stat-label {font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; color: #64748B; font-weight: 600;}
.stat-value {font-size: 1.65rem; font-weight: 700; color: #0F172A; line-height: 1.2;}
.stat-sub {font-size: .8rem; color: #64748B;}
.card {background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: .8rem 1.2rem;}
.subj-row {display: flex; align-items: center; gap: .8rem; margin: .75rem 0;}
.subj-name {width: 30%; font-weight: 600; color: #0F172A; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}
.subj-name small {display: block; font-weight: 400; color: #64748B; font-size: .75rem;}
.subj-bar {flex: 1; height: 9px; background: #E2E8F0; border-radius: 99px; overflow: hidden;}
.subj-fill {height: 100%; border-radius: 99px;}
.subj-pct {width: 54px; text-align: right; font-weight: 600; color: #334155;}
.badge {color: #fff; font-weight: 700; font-size: .78rem; padding: .18rem .6rem; border-radius: 6px; min-width: 38px; text-align: center;}
.predict {background: #E6F4F1; border: 1px solid #A7D7CF; border-radius: 12px; padding: 1.1rem 1.4rem;}
.predict .big {font-size: 2.3rem; font-weight: 700; color: #0F766E; line-height: 1.2;}
.footer-note {text-align: center; color: #94A3B8; font-size: .82rem; margin-top: 2rem;}
</style>
""", unsafe_allow_html=True)

# ---------------- State ----------------
ss = st.session_state
ss.setdefault("scale_df", pd.DataFrame(PRESETS[DEFAULT_PRESET]))
ss.setdefault("scale_ver", 0)
ss.setdefault("result", None)
ss.setdefault("details", {})
ss.setdefault("advice", "")
ss.setdefault("chat", [])


def load_preset():
    ss.scale_df = pd.DataFrame(PRESETS[ss.preset])
    ss.scale_ver += 1


def grade_colors(scale):
    n = len(scale)
    return {s["grade"]: PALETTE[round(i * (len(PALETTE) - 1) / max(n - 1, 1))] for i, s in enumerate(scale)}


def stat_card(label, value, sub, icon, color):
    return (f'<div class="stat-card"><div class="stat-icon" style="background:{color}1A;color:{color}">'
            f'{svg(icon)}</div><div><div class="stat-label">{label}</div>'
            f'<div class="stat-value">{value}</div><div class="stat-sub">{sub}</div></div></div>')


# ---------------- Hero ----------------
st.markdown(f"""
<div class="hero"><div class="hero-icon">{svg("cap", 30, "#fff")}</div>
<div><h1>Student Grade Advisor</h1>
<p>Calculate your grades and GPA with your own grading system, predict your final result and get a study plan.</p></div></div>
""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.subheader(":material/tune: Your details")
    st.caption("Optional. They improve the prediction and the advice.")
    study_hours = st.number_input("Study hours per week", 0, 100, 0)
    absences = st.number_input("Absences this term", 0, 200, 0)
    prev_pct = st.number_input("Previous term overall % (0 if none)", 0.0, 100.0, 0.0)
    failures = st.number_input("Past failed subjects", 0, 5, 0)
    goal = st.text_input("Your goal", placeholder="e.g. reach 3.5 GPA")
    st.divider()
    st.caption(f":material/smart_toy: AI model: `{advisor.PRIMARY_MODEL}`")
    with st.expander("Check available models"):
        if st.button("List models for my key"):
            try:
                st.write(advisor.list_models())
            except Exception as e:
                st.error(str(e))
        st.caption("Set GEMINI_MODEL in .env to change the model.")

tab_marks, tab_scale, tab_chat = st.tabs([
    ":material/calculate: Marks and results",
    ":material/rule: Grading system",
    ":material/chat: AI chat",
])

# ---------------- Tab 2: grading system (runs first so tab 1 can use it) ----------------
with tab_scale:
    st.subheader("Your grading system")
    st.caption("Pick a preset, then edit the table to match your institution. "
               "Add rows for more grades. GPA points can use any maximum (4.0, 5.0, 10...).")
    c1, c2 = st.columns([2, 1])
    c1.selectbox("Start from a preset", list(PRESETS), key="preset", on_change=load_preset)
    pass_mark = c2.number_input("Pass mark (%)", 0.0, 100.0, 50.0, key="pass_mark")

    scale_edit = st.data_editor(
        ss.scale_df, num_rows="dynamic", hide_index=True, key=f"scale_{ss.scale_ver}",
        column_config={
            "Grade": st.column_config.TextColumn("Grade"),
            "Min %": st.column_config.NumberColumn("Minimum %", min_value=0.0, max_value=100.0, format="%.1f"),
            "GPA points": st.column_config.NumberColumn("GPA points", min_value=0.0, format="%.2f"),
        },
    )
    scale, scale_errors = clean_scale(scale_edit.to_dict("records"))
    if scale_errors:
        for e in dict.fromkeys(scale_errors):
            st.error(e)
    else:
        st.success(f"Grading system is valid. Highest GPA points: {max(s['points'] for s in scale):g}")

# ---------------- Tab 1: marks and results ----------------
with tab_marks:
    st.subheader("Your marks")
    default = pd.DataFrame({
        "Subject": ["Math", "Physics", "English"],
        "Marks": [78.0, 55.0, 88.0],
        "Total": [100.0, 100.0, 100.0],
        "Credit hours": [3.0, 3.0, 2.0],
    })
    table = st.data_editor(
        default, num_rows="dynamic", hide_index=True,
        column_config={
            "Subject": st.column_config.TextColumn("Subject", required=True),
            "Marks": st.column_config.NumberColumn("Marks obtained", min_value=0.0, format="%.1f"),
            "Total": st.column_config.NumberColumn("Total marks", min_value=1.0, format="%.1f"),
            "Credit hours": st.column_config.NumberColumn("Credit hours", min_value=0.5, step=0.5, format="%.1f"),
        },
    )
    st.caption("Click the empty bottom row to add a subject. Select a row and press Delete to remove it.")

    if st.button("Analyze my results", type="primary", icon=":material/auto_awesome:"):
        subjects, errors = {}, []
        for _, row in table.iterrows():
            name = str(row["Subject"]).strip() if pd.notna(row["Subject"]) else ""
            if not name or name == "None":
                continue
            marks, total, cr = row["Marks"], row["Total"], row["Credit hours"]
            if name in subjects:
                errors.append(f"{name}: subject name is used twice.")
            elif pd.isna(marks) or pd.isna(total) or total <= 0:
                errors.append(f"{name}: enter valid marks and a total above 0.")
            elif marks < 0 or marks > total:
                errors.append(f"{name}: marks must be between 0 and {total:g}.")
            elif pd.isna(cr) or cr <= 0:
                errors.append(f"{name}: credit hours must be above 0.")
            else:
                subjects[name] = (float(marks), float(total), float(cr))

        if scale_errors:
            st.error("Fix your grading system first (see the Grading system tab).")
        elif errors:
            for e in errors:
                st.error(e)
        elif not subjects:
            st.warning("Please enter at least one subject.")
        else:
            result = analyze(subjects, scale, pass_mark)
            prev = prev_pct if prev_pct > 0 else result["overall_percentage"]
            predicted = predict_final(prev, result["overall_percentage"], study_hours, failures, absences)
            details = {"study_hours": study_hours, "absences": absences,
                       "goal": goal, "predicted": predicted}
            with st.spinner("Preparing your personal plan..."):
                advice = advisor.get_advice(result, details)
            ss.result, ss.details, ss.advice = result, details, advice

    # ---- Results (kept in session state so they survive chat messages) ----
    result = ss.result
    if result:
        colors = grade_colors(result["scale"])
        overall = result["overall_percentage"]
        passed = overall >= result["pass_mark"]

        st.subheader("Your results")
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(stat_card("Overall", f"{overall}%",
                              "Passing" if passed else "Below pass mark", "percent", "#0F766E"),
                    unsafe_allow_html=True)
        c2.markdown(stat_card("Overall grade", html.escape(result["overall_grade"]),
                              "credit-weighted", "award", colors[result["overall_grade"]]),
                    unsafe_allow_html=True)
        c3.markdown(stat_card("GPA", f"{result['overall_gpa']}", f"out of {result['max_points']:g}",
                              "chart", "#2563EB"), unsafe_allow_html=True)
        c4.markdown(stat_card("Needs focus", html.escape(result["weakest"]),
                              f"strongest: {html.escape(result['strongest'])}", "flag", "#DC2626"),
                    unsafe_allow_html=True)

        left, right = st.columns(2, gap="large")
        with left:
            st.subheader("Subject breakdown")
            rows = ""
            for name, r in result["subjects"].items():
                col = colors[r["grade"]]
                rows += (f'<div class="subj-row"><div class="subj-name">{html.escape(name)}'
                         f'<small>{r["credits"]:g} credit hours</small></div>'
                         f'<div class="subj-bar"><div class="subj-fill" style="width:{r["percentage"]}%;background:{col}"></div></div>'
                         f'<div class="subj-pct">{r["percentage"]}%</div>'
                         f'<span class="badge" style="background:{col}">{html.escape(r["grade"])}</span></div>')
            st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True)

        with right:
            st.subheader("Performance chart")
            cdf = pd.DataFrame({
                "Subject": list(result["subjects"].keys()),
                "Percentage": [r["percentage"] for r in result["subjects"].values()],
                "Grade": [r["grade"] for r in result["subjects"].values()],
            })
            bars = alt.Chart(cdf).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x=alt.X("Subject:N", sort=None, axis=alt.Axis(labelAngle=0, title=None)),
                y=alt.Y("Percentage:Q", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("Grade:N", legend=None,
                                scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values()))),
                tooltip=["Subject", "Percentage", "Grade"],
            )
            line = alt.Chart(pd.DataFrame({"y": [result["pass_mark"]]})).mark_rule(
                strokeDash=[6, 4], color="#64748B").encode(y="y:Q")
            st.altair_chart((bars + line).properties(height=260))
            st.caption(f"Dashed line = {result['pass_mark']:g}% pass mark")

        predicted = ss.details.get("predicted")
        st.subheader("Predicted final result")
        if predicted is not None:
            diff = round(predicted - overall, 1)
            tone = "#15803D" if diff >= 0 else "#DC2626"
            word = "above" if diff > 0 else ("below" if diff < 0 else "equal to")
            st.markdown(
                f'<div class="predict"><div class="big">{predicted}%</div>'
                f'<div style="color:{tone};font-weight:600">{abs(diff)} points {word} your current {overall}%</div>'
                f'<div style="color:#64748B;font-size:.85rem;margin-top:.35rem">'
                f'Estimate from a machine learning model trained on student data. A guide, not a guarantee.</div></div>',
                unsafe_allow_html=True)
        else:
            st.info("Prediction unavailable. Put student-mat.csv in the project folder and run `python train_model.py`.")

        st.subheader("How to improve")
        with st.container(border=True):
            st.markdown(ss.advice)
        st.caption(f"Written by {advisor.LAST_MODEL}. Ask follow-up questions in the AI chat tab.")

        out = pd.DataFrame(result["subjects"]).T[["marks", "total", "credits", "percentage", "grade", "points"]]
        st.download_button("Download results (CSV)", out.to_csv().encode("utf-8"),
                           "my_results.csv", "text/csv", icon=":material/download:")
        st.caption("If you change marks or the grading system, click Analyze again to refresh.")

# ---------------- Tab 3: chat ----------------
with tab_chat:
    st.subheader("Ask your advisor")
    if ss.result:
        st.caption("The advisor can see your results, so you can ask things like "
                   "\"How can I raise my GPA to 3.5?\" or \"What should I study first?\"")
    else:
        st.info("Analyze your marks first for personalized answers. You can still ask general study questions.")

    for m in ss.chat:
        with st.chat_message(m["role"], avatar=":material/person:" if m["role"] == "user" else ":material/smart_toy:"):
            st.markdown(m["content"])

    if prompt := st.chat_input("Ask about your results or how to study better"):
        ss.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            with st.spinner("Thinking..."):
                reply = advisor.chat_reply(ss.chat, ss.result, ss.details)
            st.markdown(reply)
        ss.chat.append({"role": "assistant", "content": reply})

    if ss.chat and st.button("Clear chat", icon=":material/delete:"):
        ss.chat = []
        st.rerun()

st.markdown('<div class="footer-note">Built with Python, Streamlit, scikit-learn and Gemini. '
            'Predictions and advice are guidance, not an official academic assessment.</div>',
            unsafe_allow_html=True)