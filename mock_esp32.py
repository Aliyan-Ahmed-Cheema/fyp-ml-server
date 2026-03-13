import requests
import time
import random

# UPDATE THIS WITH YOUR REAL PATIENT UUID
PATIENT_UUID = "4d954c49-49a5-4736-8381-498addd0a8df"
SERVER_URL = "http://127.0.0.1:5000/predict"

print(f"🚀 Starting Continuous ESP32 Stress Test for Patient: {PATIENT_UUID}...\n")

while True:
    # 1. Randomly pick a physical state
    motion_type = random.choice(["Resting", "Walking", "Running", "Resting", "Resting"]) # Weighted toward resting
    
    # 2. Generate realistic fluctuations based on the state
    if motion_type == "Resting":
        acc = [0.05, 0.1, 0.98]
        hr = random.randint(65, 80)
        ppg = random.randint(500, 515)
    elif motion_type == "Walking":
        acc = [0.5, 1.2, 0.8]
        hr = random.randint(85, 110)
        ppg = random.randint(515, 530)
    else: # Running
        acc = [1.5, 2.5, 1.2]
        hr = random.randint(115, 150)
        ppg = random.randint(530, 560)

    # 3. Build the payload
    payload = {
        "patient_id": PATIENT_UUID,
        "PPG_Signal": ppg, 
        "Heart_Rate": hr, 
        "Systolic_Peak": ppg + 10, 
        "Diastolic_Peak": ppg - 10, 
        "Pulse_Area": float(ppg * 0.75),
        "acc_x": acc[0], "acc_y": acc[1], "acc_z": acc[2]
    }

    # 4. Fire to the Python Server
    try:
        response = requests.post(SERVER_URL, json=payload)
        if response.status_code == 200:
            result = response.json()
            glucose = round(result['predicted_glucose_mg_dl'], 1)
            motion = result['motion_detected']
            
            # Print a nice visual log
            if glucose > 180 or glucose < 70:
                print(f"⚠️ [ALERT] {motion.ljust(18)} | Glucose: {glucose} mg/dL")
            else:
                print(f"✅ [OK]    {motion.ljust(18)} | Glucose: {glucose} mg/dL")
        else:
            print(f"❌ Server Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the Flask server running?")
        
    # Wait 2.5 seconds before the next reading (simulates hardware loop delay)
    time.sleep(2.5)