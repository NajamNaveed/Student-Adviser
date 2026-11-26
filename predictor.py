import joblib

_model = None

def _study_category(hours):
    # dataset scale: 1 = <2h, 2 = 2-5h, 3 = 5-10h, 4 = >10h per week
    if hours < 2: return 1
    if hours <= 5: return 2
    if hours <= 10: return 3
    return 4

def predict_final(prev_pct, current_pct, study_hours, failures, absences):
    """Returns predicted final percentage, or None if the model is missing."""
    global _model
    try:
        if _model is None:
            _model = joblib.load("model.pkl")
        row = [[prev_pct / 100 * 20, current_pct / 100 * 20,
                _study_category(study_hours), failures, absences]]
        pred = _model.predict(row)[0] / 20 * 100
        return round(max(0, min(100, pred)), 1)
    except Exception:
        return None