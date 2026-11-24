import geopandas as gpd
import pandas as pd
import os

# ---- Step 1: Load shapefile ----
shapefile_path = r"C:\Users\tanvi\OneDrive\Desktop\final prj\wildfire_with_gmail_alerts\wildfire\data\California_Fire_Perimeters_(all).shp"

if not os.path.exists(shapefile_path):
    raise FileNotFoundError(f"Shapefile not found at: {shapefile_path}")

print("📂 Loading shapefile...")
gdf = gpd.read_file(shapefile_path)

# ---- Step 2: Clean and extract centroids ----
print("📍 Extracting centroids...")
gdf["latitude"] = gdf.geometry.centroid.y
gdf["longitude"] = gdf.geometry.centroid.x

# ---- Step 3: Select useful columns ----
cols = [
    "YEAR_", "STATE", "AGENCY", "UNIT_ID", "FIRE_NAME",
    "ALARM_DATE", "GIS_ACRES", "CAUSE", "latitude", "longitude"
]

# Filter only columns that exist in the shapefile
cols = [c for c in cols if c in gdf.columns]

df = gdf[cols].copy()

# ---- Step 4: Clean data ----
df = df.dropna(subset=["latitude", "longitude"])
df = df[df["latitude"] != 0]
df = df[df["longitude"] != 0]

# ---- Step 5: Save to CSV ----
output_path = os.path.join(os.path.dirname(shapefile_path), "wildfire_dataset_clean.csv")
df.to_csv(output_path, index=False)

print(f"✅ Processed {len(df)} fire records and saved to: {output_path}")
print(df.head())

