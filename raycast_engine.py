import re
import pandas as pd
import numpy as np
import glob
import os

def process_air3_telemetry(directory_path='./'):
    print("[INFO] Initiating Air 3 Telemetry Extraction & Raycasting...")
    all_data = []
    srt_files = glob.glob(os.path.join(directory_path, '*.SRT'))
    
    if not srt_files:
        return "❌ Bro, put the SRT files in the same folder as this script."

    time_re = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->')
    lat_re = re.compile(r'\[latitude:\s*(-?\d+\.\d+)\]', re.IGNORECASE)
    lon_re = re.compile(r'\[longitude:\s*(-?\d+\.\d+)\]', re.IGNORECASE)
    alt_re = re.compile(r'\[rel_alt:\s*(-?\d+\.\d+)', re.IGNORECASE)

    # --- PHASE 1: EXTRACTION ---
    for file_path in srt_files:
        filename = os.path.basename(file_path)
        
        # Apply the specific assignment parameters based on the file name
        if '0017' in filename:
            target_pitch = -45.0
            fallback_alt = 120.0
            print(f"📄 Detected v1 (0017): Applying 120m @ 45° parameters.")
        elif '0019' in filename:
            target_pitch = -45.0
            fallback_alt = 50.0
            print(f"📄 Detected v2 (0019): Applying 50m @ 45° parameters.")
        else:
            target_pitch = -60.0
            fallback_alt = 119.0
            print(f"⚠️ Unknown file {filename}: Applying default 119m @ 60°.")

        lines = []
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
                        'source_file': filename,
                        'timestamp': current_timestamp,
                        'drone_lat': float(lat_m.group(1)),
                        'drone_lon': float(lon_m.group(1)),
                        'altitude': float(alt_m.group(1)) if alt_m else fallback_alt,
                        'pitch': target_pitch
                    })
                    current_timestamp = None 
                    
    if not all_data:
        return "❌ Extraction failed. No data found."

    df = pd.DataFrame(all_data)
    
    # --- PHASE 2: RAYCASTING & YAW MATH ---
    print("[INFO] Calculating Trajectory Yaw and Raycasting Target Coordinates...")
    R = 6378137.0 # Earth radius in meters
    
    # Calculate Yaw per file so the trajectory doesn't bleed between flights
    df['estimated_yaw'] = np.nan
    for file, group in df.groupby('source_file'):
        lat_rad = np.radians(group['drone_lat'])
        lon_rad = np.radians(group['drone_lon'])
        
        delta_lon = lon_rad.shift(-1) - lon_rad
        lat_rad_next = lat_rad.shift(-1)
        
        x = np.sin(delta_lon) * np.cos(lat_rad_next)
        y = np.cos(lat_rad) * np.sin(lat_rad_next) - np.sin(lat_rad) * np.cos(lat_rad_next) * np.cos(delta_lon)
        
        initial_bearing = np.degrees(np.arctan2(x, y))
        yaw = (initial_bearing + 360) % 360
        
        # Hover fix: ignore yaw if drone barely moved
        lat_diff = group['drone_lat'].diff().abs()
        lon_diff = group['drone_lon'].diff().abs()
        is_hovering = (lat_diff < 1e-6) & (lon_diff < 1e-6)
        
        yaw.loc[is_hovering] = np.nan
        df.loc[group.index, 'estimated_yaw'] = yaw.ffill()

    df['estimated_yaw'] = df['estimated_yaw'].ffill() # Catch any stragglers
    
    # Calculate ground distance. (tan(45) = 1, so distance = altitude)
    pitch_clipped = np.clip(df['pitch'], -89.9, -0.1)
    ground_distance = df['altitude'] * np.tan(np.radians(90 + pitch_clipped))
    
    # Project the target point using flat-earth approximation
    yaw_rad = np.radians(df['estimated_yaw'])
    lat_rad_current = np.radians(df['drone_lat'])
    
    delta_lat = (ground_distance * np.cos(yaw_rad) / R)
    delta_lon = (ground_distance * np.sin(yaw_rad) / (R * np.cos(lat_rad_current)))
    
    df['target_lat'] = df['drone_lat'] + np.degrees(delta_lat)
    df['target_lon'] = df['drone_lon'] + np.degrees(delta_lon)
    
    # --- PHASE 3: SAVE TO HARD DRIVE ---
    output_filename = 'final_air3_targets.csv'
    df.to_csv(output_filename, index=False)
    print(f"✅ SUCCESS! Data locked and loaded into '{output_filename}'")
    
    return df

# ACTUALLY RUN THE SCRIPT
df_results = process_air3_telemetry('./')
if isinstance(df_results, pd.DataFrame):
    print("\nPreview of the payload:")
    print(df_results[['source_file', 'timestamp', 'drone_lat', 'target_lat', 'estimated_yaw']].head())