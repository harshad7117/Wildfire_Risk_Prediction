"""
train_model.py

Usage:
    python train_model.py

This script:
 - Loads the historical dataset (path below)
 - Detects useful features (temperature/humidity/wind/veg/lat/lon) if present
 - Detects a binary target column (fire_occurred or similar). If not found, it
   will treat all rows as historical fire events and build a spatial-only
   "model" using a KDTree + logistic approximation.
 - Trains a RandomForestClassifier when features + target available.
 - Otherwise builds a lightweight distance->probability function and stores
   enough data for the app to compute a risk score.
 - Saves "model artifact" into backend_model/wildfire_model.pkl
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KDTree

DATA_PATH = r"C:\Users\tanvi\OneDrive\Desktop\final prj\wildfire_with_gmail_alerts\wildfire\b8aeb030-140d-43d2-aa29-1a80862e3d62.csv"
MODEL_DIR = "backend_model"
MODEL_PATH = os.path.join(MODEL_DIR, "wildfire_model.pkl")
HIST_POINTS_PATH = os.path.join(MODEL_DIR, "historical_points.npy")

os.makedirs(MODEL_DIR, exist_ok=True)

def guess_columns(df):
    """Try to detect feature and target column names from common variants."""
    lower_cols = {c.lower(): c for c in df.columns}
    # possible feature names
    feature_names_map = {
        "temperature": ["temperature", "temp", "air_temp", "airtemperature"],
        "humidity": ["humidity", "humid", "rh"],
        "wind_speed": ["wind_speed", "wind", "windspeed", "wind_kmh", "wind_kph"],
        "vegetation_index": ["vegetation_index", "ndvi", "veg_index", "vegetation"],
        "latitude": ["latitude", "lat"],
        "longitude": ["longitude", "lon", "lng", "long"]
    }
    detected = {}
    for key, variants in feature_names_map.items():
        for v in variants:
            if v in lower_cols:
                detected[key] = lower_cols[v]
                break

    # target detection
    target_variants = ["fire_occurred", "fire", "burned", "burn", "wildfire", "fire_happened", "label"]
    target_col = None
    for v in target_variants:
        if v in lower_cols:
            target_col = lower_cols[v]
            break

    return detected, target_col

def train_full_model(df, detected, target_col):
    """Train RF on available features mapped by 'detected' dict."""
    feature_cols = []
    for k in ["temperature","humidity","wind_speed","vegetation_index","latitude","longitude"]:
        if detected.get(k):
            feature_cols.append(detected[k])

    # safety: at minimum need lat & lon
    if not ("latitude" in detected and "longitude" in detected):
        raise ValueError("Training requires at least latitude & longitude.")

    X = df[feature_cols].copy()
    y = df[target_col].astype(int)

    # fillna with sensible defaults (median)
    X = X.fillna(X.median())

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    print(f"Trained RandomForestClassifier — test accuracy: {acc:.3f}")
    # Save model + feature_cols
    joblib.dump({"type":"rf","model":clf,"feature_cols":feature_cols}, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

def build_spatial_model(df):
    """If no target column, build KDTree of historical fire points and store them.
    The app will compute a distance-based probability from these points.
    """
    # Expect that each row in df represents a historical fire occurrence or event.
    # We'll take unique lat/lon pairs.
    lat_col_candidates = [c for c in df.columns if c.lower() in ("latitude","lat")]
    lon_col_candidates = [c for c in df.columns if c.lower() in ("longitude","lon","lng","long")]

    if not lat_col_candidates or not lon_col_candidates:
        raise ValueError("No latitude/longitude found for spatial model construction.")

    lat_col = lat_col_candidates[0]
    lon_col = lon_col_candidates[0]

    points = df[[lat_col, lon_col]].dropna()
    points_arr = points[[lat_col, lon_col]].to_numpy()

    # Build KDTree (uses Euclidean degrees; we'll convert to haversine at runtime if needed)
    tree = KDTree(np.radians(points_arr))  # store lat/lon in radians
    # Save minimal artifact: use KDTree points + type marker
    joblib.dump({"type":"spatial","points":points_arr}, MODEL_PATH)
    print(f"Built spatial model with {len(points_arr)} points and saved to {MODEL_PATH}")

def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded dataset with {len(df)} rows and columns: {list(df.columns)}")

    detected, target_col = guess_columns(df)
    print("Detected columns mapping:", detected)
    print("Detected target column:", target_col)

    try:
        if target_col and all(k in detected for k in ("latitude","longitude")):
            # Attempt full model training. If features beside lat/lon exist, use them; otherwise RF on lat/lon
            train_full_model(df, detected, target_col)
        else:
            # Fall back to spatial-only model (historical points)
            build_spatial_model(df)
    except Exception as e:
        print("Training failed with error:", e)
        print("Attempting fallback to spatial-only model.")
        build_spatial_model(df)

if __name__ == "__main__":
    main()
