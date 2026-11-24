import pandas as pd
import os

HISTORY_FILE = "prediction_history.csv"

def save_history(lat, lon, probability):
    new_entry = pd.DataFrame([{
        "latitude": lat,
        "longitude": lon,
        "probability": probability
    }])

    if os.path.exists(HISTORY_FILE):
        old_df = pd.read_csv(HISTORY_FILE)
        updated_df = pd.concat([old_df, new_entry], ignore_index=True)
        updated_df.to_csv(HISTORY_FILE, index=False)
    else:
        new_entry.to_csv(HISTORY_FILE, index=False)

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    else:
        return pd.DataFrame(columns=["latitude", "longitude", "probability"])
