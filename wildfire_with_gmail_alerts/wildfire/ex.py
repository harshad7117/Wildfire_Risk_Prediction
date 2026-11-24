import pandas as pd

path = r"C:\Users\tanvi\OneDrive\Desktop\final prj\wildfire_with_gmail_alerts\wildfire\b8aeb030-140d-43d2-aa29-1a80862e3d62.csv"

df = pd.read_csv(path)
df['fire_occurred'] = 1   # every row marks a past fire
df.to_csv(path, index=False)

print("✅ Added target column 'fire_occurred' to dataset")
