from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import joblib
import numpy as np
import pandas as pd
from lime.lime_tabular import LimeTabularExplainer

model = joblib.load("loan_approval_model.pkl")

@csrf_exempt
def predict_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Create DataFrame with proper types
            df = pd.DataFrame({
                "Gender": [1 if data['gender'] == "Male" else 0],
                "Married": [1 if data['married'] == "Yes" else 0],
                "Dependents": [int(data['dependents']) if data['dependents'] in ["0", "1", "2"] else 3],
                "Education": [1 if data['education'] == "Graduate" else 0],
                "Self_Employed": [1 if data['self_employed'] == "Yes" else 0],
                "ApplicantIncome": [float(data['applicant_income'])],
                "CoapplicantIncome": [float(data['coapplicant_income'])],
                "LoanAmount": [float(data['loan_amount'])],
                "Loan_Amount_Term": [float(data['loan_term'])],
                "Credit_History": [float(data['credit_history'])],
                "Property_Area": [0 if data['property_area'] == "Rural" else 1 if data['property_area'] == "Semiurban" else 2],
            })

            # Make prediction
            prediction_proba = model.predict_proba(df)[0][1] * 100
            decision = "Approved" if prediction_proba > 50 else "Rejected"

            # LIME Explanation
            explainer = LimeTabularExplainer(
                training_data=np.random.rand(100, len(df.columns)),
                feature_names=df.columns.tolist(),
                mode="classification"
            )

            # Ensure the instance is a float array
            instance = df.iloc[0].values.astype(float)

            explanation = explainer.explain_instance(instance, model.predict_proba)
            factors = explanation.as_list()

            return JsonResponse({
                "status": "success",
                "prediction": decision,
                "confidence": round(prediction_proba, 2),
                "explanation": factors
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=400)
