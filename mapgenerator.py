import pandas as pd
import folium

def generate_tactical_map(csv_path, output_name):
    print(f"[INFO] Rendering Dashboard for {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Initialize the map at the drone's starting target coordinate
    start_lat = df['target_lat'].iloc[0]
    start_lon = df['target_lon'].iloc[0]
    m = folium.Map(location=[start_lat, start_lon], zoom_start=18, max_zoom=22)
    
    # 1. Draw the continuous target path (The blue laser trail)
    path_coords = list(zip(df['target_lat'], df['target_lon']))
    folium.PolyLine(path_coords, color="blue", weight=2, opacity=0.4, popup="Camera Sweep Path").add_to(m)
    
    # 2. Filter out the boring stuff to find the actual targets
    hits = df[df['detected_object'] != 'Asphalt/Dirt']
    print(f"🎯 Locked onto {len(hits)} targets out of {len(df)} total frames.")
    
    # 3. Drop tactical markers for every confirmed vehicle/pedestrian
    for _, row in hits.iterrows():
        obj_type = str(row['detected_object']).lower()
        
        # Color coding: Cars are red, anything else (trucks/pedestrians) is orange
        marker_color = "red" if "car" in obj_type else "orange"
        
        folium.CircleMarker(
            location=[row['target_lat'], row['target_lon']],
            radius=3,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7,
            popup=f"{row['timestamp']} | {obj_type.upper()}"
        ).add_to(m)
        
    m.save(output_name)
    print(f"✅ Tactical map saved to {output_name}. Open it in your web browser.")

# Fire it up for both of your fused CSVs
generate_tactical_map('FUSED_DJI_20260427152226_0017_D.csv', 'v1_tactical_map.html')
generate_tactical_map('FUSED_DJI_20260427152735_0019_D.csv', 'v2_tactical_map.html')