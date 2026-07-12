import tkinter as tk
from tkinter import ttk
import requests
import time
import random
import threading

# UPDATE THIS WITH YOUR REAL PATIENT UUID
PATIENT_UUID = "4d954c49-49a5-4736-8381-498addd0a8df"
SERVER_URL = "https://aliyan.pythonanywhere.com/predict"

class ESP32Simulator:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ GlucoSense ESP32 Hardware Simulator")
        self.root.geometry("450x600") # Slightly increased height to fit new inputs
        self.root.configure(padx=20, pady=20)

        # --- Internal States ---
        self.glucose_state = "Normal"
        self.motion_state = "Resting"
        self.is_running = True

        # --- Tkinter String Variables for Live Updating ---
        self.live_ppg = tk.StringVar(value="---")
        self.live_pulse_area = tk.StringVar(value="---")
        self.live_glucose = tk.StringVar(value="---")
        self.status_msg = tk.StringVar(value="System Initializing...")

        self.setup_ui()

        # Start the background thread for sending data
        self.worker_thread = threading.Thread(target=self.sensor_loop, daemon=True)
        self.worker_thread.start()

    def set_glucose(self, state):
        self.glucose_state = state
        self.status_msg.set(f"State updated: {self.glucose_state} | {self.motion_state}")

    def set_motion(self, state):
        self.motion_state = state
        self.status_msg.set(f"State updated: {self.glucose_state} | {self.motion_state}")

    def clear_overrides(self):
        self.custom_ppg_entry.delete(0, tk.END)
        self.custom_pa_entry.delete(0, tk.END)
        self.status_msg.set("Overrides cleared. Back to auto-generation.")

    def setup_ui(self):
        # 1. LIVE MONITOR
        monitor_frame = tk.LabelFrame(self.root, text=" Live Telemetry ", font=("Arial", 12, "bold"), pady=10)
        monitor_frame.pack(fill="x", pady=(0, 15))

        tk.Label(monitor_frame, text="Sent PPG:", font=("Arial", 10)).grid(row=0, column=0, padx=10, sticky="e")
        tk.Label(monitor_frame, textvariable=self.live_ppg, font=("Arial", 14, "bold"), fg="blue").grid(row=0, column=1, sticky="w")

        tk.Label(monitor_frame, text="Sent Pulse Area:", font=("Arial", 10)).grid(row=1, column=0, padx=10, sticky="e")
        tk.Label(monitor_frame, textvariable=self.live_pulse_area, font=("Arial", 14, "bold"), fg="purple").grid(row=1, column=1, sticky="w")

        tk.Label(monitor_frame, text="Received Glucose:", font=("Arial", 10)).grid(row=2, column=0, padx=10, sticky="e")
        tk.Label(monitor_frame, textvariable=self.live_glucose, font=("Arial", 14, "bold"), fg="red").grid(row=2, column=1, sticky="w")

        # 2. GLUCOSE CONTROLS
        gluc_frame = tk.LabelFrame(self.root, text=" Sim: Blood Sugar State ", font=("Arial", 10, "bold"), pady=10)
        gluc_frame.pack(fill="x", pady=5)
        
        tk.Button(gluc_frame, text="Hypoglycemia (Low)", bg="#ff9999", command=lambda: self.set_glucose("Hypoglycemia")).pack(side="left", expand=True, padx=2)
        tk.Button(gluc_frame, text="Normal", bg="#99ff99", command=lambda: self.set_glucose("Normal")).pack(side="left", expand=True, padx=2)
        tk.Button(gluc_frame, text="Hyperglycemia (High)", bg="#ffcc99", command=lambda: self.set_glucose("Hyperglycemia")).pack(side="left", expand=True, padx=2)

        # 3. MOTION CONTROLS
        motion_frame = tk.LabelFrame(self.root, text=" Sim: Physical Motion ", font=("Arial", 10, "bold"), pady=10)
        motion_frame.pack(fill="x", pady=5)

        tk.Button(motion_frame, text="Standing/Still", bg="#e6e6e6", command=lambda: self.set_motion("Resting")).pack(side="left", expand=True, padx=2)
        tk.Button(motion_frame, text="Walking", bg="#cce5ff", command=lambda: self.set_motion("Walking")).pack(side="left", expand=True, padx=2)
        tk.Button(motion_frame, text="Running", bg="#ffcce5", command=lambda: self.set_motion("Running")).pack(side="left", expand=True, padx=2)

        # 4. CUSTOM OVERRIDES
        custom_frame = tk.LabelFrame(self.root, text=" Custom Sensor Overrides ", font=("Arial", 10, "bold"), pady=10)
        custom_frame.pack(fill="x", pady=5)

        # PPG Input
        ppg_frame = tk.Frame(custom_frame)
        ppg_frame.pack(fill="x", pady=2)
        tk.Label(ppg_frame, text="Force PPG Value:").pack(side="left", padx=5)
        self.custom_ppg_entry = tk.Entry(ppg_frame, width=10)
        self.custom_ppg_entry.pack(side="left", padx=5)

        # Pulse Area Input
        pa_frame = tk.Frame(custom_frame)
        pa_frame.pack(fill="x", pady=2)
        tk.Label(pa_frame, text="Force Pulse Area:").pack(side="left", padx=5)
        self.custom_pa_entry = tk.Entry(pa_frame, width=10)
        self.custom_pa_entry.pack(side="left", padx=5)

        # Clear Button
        tk.Button(custom_frame, text="Clear Overrides", command=self.clear_overrides).pack(pady=5)

        # 5. STATUS BAR
        tk.Label(self.root, textvariable=self.status_msg, font=("Arial", 9, "italic"), fg="gray").pack(side="bottom", pady=10)

    def sensor_loop(self):
        """Background thread that constantly fires to the Flask server."""
        while self.is_running:
            # 1. Generate base values according to selected state
            if self.glucose_state == "Normal":
                ppg = random.randint(506, 517)
                hr = random.randint(61, 93)
                pulse_area = random.randint(310, 480)
            elif self.glucose_state == "Hypoglycemia":
                ppg = random.randint(518, 528) 
                hr = random.randint(95, 120)
                pulse_area = random.randint(480, 560)
            else: # Hyperglycemia
                ppg = random.randint(485, 505) 
                hr = random.randint(65, 85)
                pulse_area = random.randint(250, 310)

            # 2. Check for UI Overrides
            custom_ppg_val = self.custom_ppg_entry.get().strip()
            custom_pa_val = self.custom_pa_entry.get().strip()
            
            overrides_active = []

            if custom_ppg_val.lstrip('-').isdigit(): # Allows negative numbers just in case
                ppg = int(custom_ppg_val)
                overrides_active.append(f"PPG: {ppg}")
            
            # Replace a single decimal point to check if it's a valid float
            if custom_pa_val.replace('.', '', 1).lstrip('-').isdigit():
                pulse_area = float(custom_pa_val)
                overrides_active.append(f"Area: {pulse_area}")

            # Update status bar if overrides are used
            if overrides_active:
                override_str = " | ".join(overrides_active)
                self.root.after(0, self.status_msg.set, f"⚠️ Using Forced Data -> {override_str}")

            # 3. Assign Accelerometer based on selected motion
            if self.motion_state == "Resting":
                acc = [0.05, 0.1, 0.98]
            elif self.motion_state == "Walking":
                acc = [0.5, 1.2, 0.8]
            else: # Running
                acc = [1.5, 2.5, 1.2]

            sys_peak = ppg + 10
            dia_peak = ppg - 5

            # 4. Build Payload
            payload = {
                "patient_id": PATIENT_UUID,
                "PPG_Signal": ppg, 
                "Heart_Rate": hr, 
                "Systolic_Peak": sys_peak, 
                "Diastolic_Peak": dia_peak, 
                "Pulse_Area": float(pulse_area),
                "acc_x": acc[0], "acc_y": acc[1], "acc_z": acc[2]
            }

            # 5. Fire Request
            try:
                response = requests.post(SERVER_URL, json=payload, timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    glucose = round(result['predicted_glucose_mg_dl'], 1)
                    
                    # Update GUI safely from the background thread
                    self.root.after(0, self.live_ppg.set, str(ppg))
                    self.root.after(0, self.live_pulse_area.set, str(pulse_area))
                    self.root.after(0, self.live_glucose.set, f"{glucose} mg/dL")
                else:
                    self.root.after(0, self.status_msg.set, f"❌ Server Error {response.status_code}")
            except Exception as e:
                self.root.after(0, self.status_msg.set, "❌ Connection Error: Is Flask running?")
                
            time.sleep(2.5)

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = ESP32Simulator(root)
    root.mainloop()