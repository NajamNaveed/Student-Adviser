import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

FEATURES = ["G1", "G2", "studytime", "failures", "absences"]

df = pd.read_csv("student-mat.csv", sep=";")   # this file uses ; as separator
X, y = df[FEATURES], df["G3"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

mae = mean_absolute_error(y_test, model.predict(X_test))
print(f"Average error: {mae:.2f} marks out of 20")

joblib.dump(model, "model.pkl")
print("Saved model.pkl")