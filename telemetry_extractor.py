import re
import pandas as pd
import glob
import os

def extract_dji_telemetry(directory_path='./'):
    all_data = []
    srt_files = glob.glob(os.path.join(directory_path, '*.SRT'))
    
    time_re = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->')
    lat_re = re.compile(r'\[latitude:\s*(-?\d+\.\d+)\]', re.IGNORECASE)
    lon_re = re.compile(r'\[longitude:\s*(-?\d+\.\d+)\]', re.IGNORECASE)
    alt_re = re.compile(r'\[rel_alt:\s*(-?\d+\.\d+)', re.IGNORECASE)

    for file_path in srt_files:
        lines = []
        # We know it's utf-8-sig now, but keep the fallback just in case DJI updates their firmware again
        for enc in ['utf-8-sig', 'utf-8', 'utf-16']:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
                
        current_timestamp = None
        
        for line in lines:
            t_match = time_re.search(line)
            if t_match:
                current_timestamp = t_match.group(1)
            
            if '[latitude:' in line.lower() or 'iso' in line.lower():
                lat_m = lat_re.search(line)
                lon_m = lon_re.search(line)
                alt_m = alt_re.search(line)
                
                if lat_m and lon_m and current_timestamp:
                    all_data.append({
                        'source_file': os.path.basename(file_path),
                        'timestamp': current_timestamp,
                        'latitude': float(lat_m.group(1)),
                        'longitude': float(lon_m.group(1)),
                        'altitude': float(alt_m.group(1)) if alt_m else 0.0,
                        'gimbal_pitch': -60.0 # From assignment spec 
                    })
                    current_timestamp = None 
                    
    df = pd.DataFrame(all_data)
    # Convert timestamp to a proper datetime object so you can actually sync it with video frames
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%H:%M:%S,%f').dt.time
    return df

# 1. Run the function to get the DataFrame (make sure the path is correct)
df = extract_dji_telemetry('./')

# 2. ACTUALLY SAVE IT TO YOUR HARD DRIVE
if not df.empty:
    df.to_csv('cleaned_drone_telemetry.csv', index=False)
    print("✅ Data successfully saved to cleaned_drone_telemetry.csv.")
else:
    print("❌ DataFrame is empty. Nothing to save.")