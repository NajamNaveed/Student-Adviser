PRESETS = {
    "Standard (4.0)": [
        {"Grade": "A+", "Min %": 90.0, "GPA points": 4.0},
        {"Grade": "A", "Min %": 80.0, "GPA points": 4.0},
        {"Grade": "B", "Min %": 70.0, "GPA points": 3.0},
        {"Grade": "C", "Min %": 60.0, "GPA points": 2.0},
        {"Grade": "D", "Min %": 50.0, "GPA points": 1.0},
        {"Grade": "F", "Min %": 0.0, "GPA points": 0.0},
    ],
    "Plus / minus (4.0)": [
        {"Grade": "A", "Min %": 90.0, "GPA points": 4.0},
        {"Grade": "A-", "Min %": 85.0, "GPA points": 3.7},
        {"Grade": "B+", "Min %": 80.0, "GPA points": 3.3},
        {"Grade": "B", "Min %": 75.0, "GPA points": 3.0},
        {"Grade": "B-", "Min %": 70.0, "GPA points": 2.7},
        {"Grade": "C+", "Min %": 65.0, "GPA points": 2.3},
        {"Grade": "C", "Min %": 60.0, "GPA points": 2.0},
        {"Grade": "D", "Min %": 50.0, "GPA points": 1.0},
        {"Grade": "F", "Min %": 0.0, "GPA points": 0.0},
    ],
}
DEFAULT_PRESET = "Standard (4.0)"


def _missing(v):
    return v is None or (isinstance(v, float) and v != v) or str(v).strip() in ("", "None", "nan")


def clean_scale(rows):
    """Validate the grade table. Returns (scale sorted high to low, list of errors)."""
    scale, errors, seen = [], [], set()
    for r in rows:
        g, m, p = r.get("Grade"), r.get("Min %"), r.get("GPA points")
        if _missing(g) and _missing(m) and _missing(p):
            continue
        if _missing(g) or _missing(m) or _missing(p):
            errors.append("Every grade row needs a name, a minimum % and GPA points.")
            continue
        g = str(g).strip()
        if g in seen:
            errors.append(f"Grade '{g}' appears more than once.")
            continue
        if not 0 <= float(m) <= 100:
            errors.append(f"{g}: minimum % must be between 0 and 100.")
            continue
        if float(p) < 0:
            errors.append(f"{g}: GPA points cannot be negative.")
            continue
        seen.add(g)
        scale.append({"grade": g, "min": float(m), "points": float(p)})
    scale.sort(key=lambda s: s["min"], reverse=True)
    if not scale:
        errors.append("Add at least one grade.")
    elif scale[-1]["min"] > 0:
        errors.append("The lowest grade must start at 0% so every mark gets a grade.")
    return scale, errors


def get_grade(pct, scale):
    for s in scale:
        if pct >= s["min"]:
            return s["grade"], s["points"]
    return scale[-1]["grade"], scale[-1]["points"]


def analyze(subjects, scale, pass_mark=50.0):
    """subjects = {"Math": (marks, total, credit_hours)}"""
    results = {}
    for name, (marks, total, credits) in subjects.items():
        pct = marks / total * 100
        grade, pts = get_grade(pct, scale)
        results[name] = {"marks": marks, "total": total, "credits": credits,
                         "percentage": round(pct, 1), "grade": grade, "points": pts}

    tc = sum(r["credits"] for r in results.values())
    overall_pct = sum(r["percentage"] * r["credits"] for r in results.values()) / tc
    overall_gpa = sum(r["points"] * r["credits"] for r in results.values()) / tc
    overall_grade, _ = get_grade(overall_pct, scale)

    return {
        "subjects": results,
        "overall_percentage": round(overall_pct, 1),
        "overall_gpa": round(overall_gpa, 2),
        "overall_grade": overall_grade,
        "max_points": max(s["points"] for s in scale),
        "total_credits": tc,
        "pass_mark": pass_mark,
        "weakest": min(results, key=lambda s: results[s]["percentage"]),
        "strongest": max(results, key=lambda s: results[s]["percentage"]),
        "scale": scale,
    }