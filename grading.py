def get_grade(percentage):
    if percentage >= 90: return "A+", 4.0
    if percentage >= 80: return "A", 4.0
    if percentage >= 70: return "B", 3.0
    if percentage >= 60: return "C", 2.0
    if percentage >= 50: return "D", 1.0
    return "F", 0.0


def analyze(subjects):
    """subjects = {"Math": (78, 100), "Physics": (55, 100)}  -> (marks, total)"""
    results = {}
    for name, (marks, total) in subjects.items():
        pct = marks / total * 100
        grade, gpa = get_grade(pct)
        results[name] = {"marks": marks, "total": total,
                         "percentage": round(pct, 1), "grade": grade, "gpa": gpa}

    overall_pct = sum(r["percentage"] for r in results.values()) / len(results)
    overall_gpa = sum(r["gpa"] for r in results.values()) / len(results)
    weakest = min(results, key=lambda s: results[s]["percentage"])
    strongest = max(results, key=lambda s: results[s]["percentage"])

    return {"subjects": results,
            "overall_percentage": round(overall_pct, 1),
            "overall_gpa": round(overall_gpa, 2),
            "weakest": weakest, "strongest": strongest}


if __name__ == "__main__":
    print(analyze({"Math": (78, 100), "Physics": (55, 100), "English": (88, 100)}))