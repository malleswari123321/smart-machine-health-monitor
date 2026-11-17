import json
import os
import time
from collections import deque
import paho.mqtt.client as mqtt
import pandas as pd
from sklearn.ensemble import IsolationForest

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
DATA_TOPIC = "madhu/factory/m1/data"
CMD_TOPIC = "madhu/factory/m1/cmd"

# Buffer to hold readings for training and sliding window
readings_buffer = deque(maxlen=100)
model = None
is_trained = False

CSV_PATH = "../data/alerts.csv"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(DATA_TOPIC)

def on_message(client, userdata, msg):
    global model, is_trained
    try:
        payload = json.loads(msg.payload.decode())
        temp = payload.get("temp")
        vib = payload.get("vib")
        
        print(f"Received telemetry -> Temperature: {temp}°C, Vibration: {vib}")

        readings_buffer.append([temp, vib])

        # Train baseline quickly on the first 5 readings for instant testing
        if not is_trained and len(readings_buffer) >= 5:
            print("Training Isolation Forest baseline on first 5 readings...")
            df_train = pd.DataFrame(list(readings_buffer), columns=["temp", "vib"])
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(df_train)
            is_trained = True
            print("Model training complete!")

        # Predict anomalies once trained, or trigger instantly if vibration spikes high
        if is_trained:
            current_data = pd.DataFrame([[temp, vib]], columns=["temp", "vib"])
            prediction = model.predict(current_data)  # -1 for anomaly, 1 for normal

            if prediction[0] == -1 or vib > 3000:
                print("⚠️ ANOMALY DETECTED! Sending ALERT command...")
                client.publish(CMD_TOPIC, "ALERT")
                log_alert(temp, vib)
            else:
                print("Status Normal. Sending OK...")
                client.publish(CMD_TOPIC, "OK")
        else:
            print("Warming up model buffer...")

    except Exception as e:
        print(f"Error processing message: {e}")

def log_alert(temp, vib):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    file_exists = os.path.isfile(CSV_PATH)
    
    df_alert = pd.DataFrame([{
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "temp": temp,
        "vib": vib,
        "status": "PENDING"
    }])
    
    df_alert.to_csv(CSV_PATH, mode='a', index=False, header=not file_exists)
    print(f"Alert logged to {CSV_PATH}")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to MQTT broker (broker.hivemq.com)...")
    client.connect("broker.hivemq.com", 1883, 60)
    
    # This keeps the script running continuously to receive messages
    client.loop_forever()