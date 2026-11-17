import os
import pandas as pd
from openpyxl import load_workbook, Workbook

# Define paths relative to the python folder
CSV_PATH = "../data/alerts.csv"
EXCEL_PATH = "../data/maintenance_tickets.xlsx"

def run_rpa_bot():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found. Run subscriber.py or trigger an alert first!")
        return

    df_alerts = pd.read_csv(CSV_PATH)
    
    # Filter for pending alerts
    pending_alerts = df_alerts[df_alerts["status"] == "PENDING"]
    
    if pending_alerts.empty:
        print("No new pending alerts found to convert into maintenance tickets.")
        return

    print(f"Processing {len(pending_alerts)} pending alert(s) into maintenance tickets...")

    # Load existing excel or create a new one if it doesn't exist
    if os.path.exists(EXCEL_PATH):
        df_tickets = pd.read_excel(EXCEL_PATH)
    else:
        df_tickets = pd.DataFrame(columns=[
            "Ticket_ID", "Timestamp", "Temperature_C", "Vibration", "Priority", "Status", "AI_Diagnostic_Notes"
        ])

    # Append new tickets from pending alerts
    for index, row in pending_alerts.iterrows():
        new_ticket_id = f"TICK-{int(row['timestamp']) if str(row['timestamp']).isdigit() else len(df_tickets) + 1001}"
        
        # Determine priority based on temperature or vibration thresholds
        priority = "HIGH" if row["temp"] > 60 or row["vib"] > 3000 else "MEDIUM"

        new_row = {
            "Ticket_ID": new_ticket_id,
            "Timestamp": row["timestamp"],
            "Temperature_C": row["temp"],
            "Vibration": row["vib"],
            "Priority": priority,
            "Status": "TICKET_CREATED",
            "AI_Diagnostic_Notes": "Automated anomaly flagged by Isolation Forest model."
        }
        
        # Append using pandas concat
        df_tickets = pd.concat([df_tickets, pd.DataFrame([new_row])], ignore_index=True)
        
        # Update status in original alerts dataframe so it doesn't duplicate
        df_alerts.loc[index, "status"] = "TICKET_CREATED"

    # Save updated files
    df_tickets.to_excel(EXCEL_PATH, index=False)
    df_alerts.to_csv(CSV_PATH, index=False)
    
    print(f"Successfully generated/updated maintenance tickets at {EXCEL_PATH}!")

if __name__ == "__main__":
    run_rpa_bot()