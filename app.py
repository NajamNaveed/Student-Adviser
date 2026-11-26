import pandas as pd
import streamlit as st
from grading import analyze
from advisor import get_advice
from predictor import predict_final

st.set_page_config(page_title="Student Advisor", page_icon="🎓", layout="centered")
st.title("🎓 Student Grade Advisor")
st.write("Enter your subjects and marks. You get your grades, GPA (out of 4), "
         "a predicted final result, and a personal improvement plan.")

# ---- 1. Marks ----
st.subheader("1. Your marks")
default = pd.DataFrame({
    "Subject": ["Math", "Physics", "English"],
    "Marks": [78.0, 55.0, 88.0],
    "Total": [100.0, 100.0, 100.0],
})
table = st.data_editor(default, num_rows="dynamic")
st.caption("Click the empty last row to add a subject. Select a row and press Delete to remove it.")

# ---- 2. Optional details ----
st.subheader("2. Optional details")
c1, c2 = st.columns(2)
study_hours = c1.number_input("Study hours per week", min_value=0, max_value=100, value=0)
absences = c2.number_input("Absences this term", min_value=0, max_value=200, value=0)
goal = st.text_input("Your goal (e.g. 'reach 3.5 GPA')")

c3, c4 = st.columns(2)
prev_pct = c3.number_input("Previous term overall % (0 if none)",
                           min_value=0.0, max_value=100.0, value=0.0)
failures = c4.number_input("Past failed subjects", min_value=0, max_value=5, value=0)

# ---- Process ----
if st.button("Get my analysis", type="primary"):
    subjects, errors = {}, []
    for _, row in table.iterrows():
        name = str(row["Subject"]).strip() if pd.notna(row["Subject"]) else ""
        if not name or name == "None":
            continue
        marks, total = row["Marks"], row["Total"]
        if pd.isna(marks) or pd.isna(total) or total <= 0:
            errors.append(f"{name}: enter valid marks and a total above 0.")
        elif marks < 0 or marks > total:
            errors.append(f"{name}: marks must be between 0 and {total:g}.")
        else:
            subjects[name] = (float(marks), float(total))

    if errors:
        for e in errors:
            st.error(e)
    elif not subjects:
        st.warning("Please enter at least one subject.")
    else:
        result = analyze(subjects)

        st.subheader("Your results")
        m1, m2, m3 = st.columns(3)
        m1.metric("Overall %", f"{result['overall_percentage']}%")
        m2.metric("GPA (out of 4)", result["overall_gpa"])
        m3.metric("Weakest subject", result["weakest"])

        df = pd.DataFrame(result["subjects"]).T
        df = df[["marks", "total", "percentage", "grade", "gpa"]]
        st.dataframe(df)
        st.bar_chart(df["percentage"].astype(float))

        # ---- ML prediction ----
        prev = prev_pct if prev_pct > 0 else result["overall_percentage"]
        predicted = predict_final(prev, result["overall_percentage"],
                                  study_hours, failures, absences)
        if predicted is not None:
            st.metric("🔮 Predicted final result", f"{predicted}%")
            st.caption("Estimate from a machine learning model. It is a guide, not a guarantee.")
        else:
            st.info("Prediction unavailable (run train_model.py to create model.pkl).")

        # ---- AI advice ----
        st.subheader("💡 How to improve")
        with st.spinner("Preparing your personal plan..."):
            advice = get_advice(
                result,
                study_hours=study_hours or None,
                absences=absences or None,
                goal=goal or None,
                predicted=predicted,
            )
        st.markdown(advice)