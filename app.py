import os
import math
import joblib
import pandas as pd
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# 1. Load the trained Random Forest model
try:
    model = joblib.load('glucose_model.pkl')
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")

# 2. Connect to Supabase
# We use environment variables so your keys stay secret on Render!
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("WARNING: Supabase credentials missing! Set them in Render environment variables.")

@app.route('/predict', methods=['POST'])
def predict_glucose():
    try:
        # 1. Receive data from the ESP32
        data = request.json
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({"error": "Missing patient_id"}), 400

        # 2. Fetch Demographic Data from Supabase
        response = supabase.table('profiles').select('age, gender, height, weight').eq('id', patient_id).execute()
        
        if not response.data:
            return jsonify({"error": "Patient not found in database or missing demographic data"}), 404
            
        patient_info = response.data[0]

        # 3. Extract Accelerometer Data & Determine Motion State
        acc_x = data.get('acc_x', 0)
        acc_y = data.get('acc_y', 0)
        acc_z = data.get('acc_z', 0)
        
        magnitude = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        
        if magnitude < 1.2:
            motion_state = "Resting / Standing"
        elif magnitude < 2.2:
            motion_state = "Walking"
        else:
            motion_state = "Running"

        # 4. Extract PPG Data
        ppg_signal = data.get('PPG_Signal', 0)
        heart_rate = data.get('Heart_Rate', 0)
        systolic_peak = data.get('Systolic_Peak', 0)
        diastolic_peak = data.get('Diastolic_Peak', 0)
        pulse_area = data.get('Pulse_Area', 0)

        # 5. Prepare Data for the Model
        # Notice we are mapping the lowercase db columns (patient_info['gender']) 
        # to the uppercase model features ('Gender')
        features = pd.DataFrame([{
            'PPG_Signal': ppg_signal,
            'Heart_Rate': heart_rate,
            'Systolic_Peak': systolic_peak,
            'Diastolic_Peak': diastolic_peak,
            'Pulse_Area': pulse_area,
            'Gender': patient_info['gender'],
            'Age': patient_info['age'],
            'Height': patient_info['height'],
            'Weight': patient_info['weight']
        }])
        
        # 6. Make Prediction
        predicted_glucose = model.predict(features)[0]

        # 7. SAVE TO SUPABASE (This updates the React website instantly!)
        supabase.table('glucose_readings').insert({
            "patient_id": patient_id,
            "mg_dl": float(predicted_glucose)
        }).execute()

        # 8. Send Response back to ESP32
        return jsonify({
            "status": "success",
            "patient_id": patient_id,
            "motion_detected": motion_state,
            "acceleration_g": round(magnitude, 2),
            "predicted_glucose_mg_dl": round(predicted_glucose, 1)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)