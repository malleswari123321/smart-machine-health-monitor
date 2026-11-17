import os
import pandas as pd
from openai import OpenAI

# Initialize OpenAI client (make sure your OPENAI_API_KEY environment variable is set)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

CSV_PATH = "../data/alerts.csv"

def generate_maintenance_reports():
    if not os.path.exists(CSV_PATH):
        print("No alerts.csv file found yet. Trigger an anomaly in Wokwi first!")
        return

    df = pd.read_csv(CSV_PATH)
    
    # Filter for pending alerts
    pending_alerts = df[df["status"] == "PENDING"]
    
    if pending_alerts.empty:
        print("No pending alerts to process.")
        return

    print(f"Found {len(pending_alerts)} pending alert(s). Generating AI maintenance reports...")

    for index, row in pending_alerts.iterrows():
        temp = row["temp"]
        vib = row["vib"]
        timestamp = row["timestamp"]

        prompt = f"""
        Generate a professional industrial maintenance report for an anomaly detected on Machine M1.
        Timestamp: {timestamp}
        Recorded Temperature: {temp}°C
        Recorded Vibration: {vib}
        
        Provide:
        1. Possible root cause analysis.
        2. Recommended corrective action for the technician.
        3. Urgency level (Low/Medium/High).
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # Fixed: Added [0] to choices list
            report_text = response.choices[0].message.content
            
            print(f"\n--- AI Maintenance Report for Alert at {timestamp} ---")
            print(report_text)
            print("-" * 60)

            # Update status to processed
            df.loc[index, "status"] = "REPORT_GENERATED"

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")

    # Save updated dataframe back to CSV
    df.to_csv(CSV_PATH, index=False)

if __name__ == "__main__":
    generate_maintenance_reports()