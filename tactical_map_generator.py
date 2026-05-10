import pandas as pd

def generate_tactical_kml(csv_path, output_path='visual_verification.kml'):
    print("[INFO] Generating Mapteah-grade KML file...")
    df = pd.read_csv(csv_path)
    
    # KML Boilerplate. Drone=Blue, Target=Red, Ray=Yellow (semi-transparent)
    kml = ['''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Optical Navigation - Raycast Verification</name>
    <Style id="dronePath"><LineStyle><color>ffff0000</color><width>4</width></LineStyle></Style>
    <Style id="targetPath"><LineStyle><color>ff0000ff</color><width>4</width></LineStyle></Style>
    <Style id="rayBeam"><LineStyle><color>7700ffff</color><width>2</width></LineStyle></Style>''']

    # Process each flight separately
    for file, group in df.groupby('source_file'):
        kml.append(f'<Folder><name>{file}</name>')
        
        # 1. Plot Drone Path (Blue)
        kml.append('<Placemark><name>Drone Trajectory</name><styleUrl>#dronePath</styleUrl><LineString>')
        kml.append('<extrude>1</extrude><tessellate>1</tessellate><altitudeMode>relativeToGround</altitudeMode><coordinates>')
        for _, row in group.iterrows():
            kml.append(f"{row['drone_lon']},{row['drone_lat']},{row['altitude']}")
        kml.append('</coordinates></LineString></Placemark>')

        # 2. Plot Target Ground Path (Red)
        kml.append('<Placemark><name>Target Ground Path</name><styleUrl>#targetPath</styleUrl><LineString>')
        kml.append('<tessellate>1</tessellate><altitudeMode>clampToGround</altitudeMode><coordinates>')
        for _, row in group.iterrows():
            kml.append(f"{row['target_lon']},{row['target_lat']},0")
        kml.append('</coordinates></LineString></Placemark>')

        # 3. Plot Raycast Beams (Every 30th frame ~ 1 second)
        kml.append('<Folder><name>Camera Rays</name>')
        for i, (_, row) in enumerate(group.iterrows()):
            if i % 30 == 0:
                kml.append('<Placemark><styleUrl>#rayBeam</styleUrl><LineString><altitudeMode>relativeToGround</altitudeMode><coordinates>')
                kml.append(f"{row['drone_lon']},{row['drone_lat']},{row['altitude']}")
                kml.append(f"{row['target_lon']},{row['target_lat']},0")
                kml.append('</coordinates></LineString></Placemark>')
        kml.append('</Folder>')
        kml.append('</Folder>')

    kml.append('  </Document>\n</kml>')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(kml))
    
    print(f"✅ KML secured: {output_path}")
    print("Download Google Earth Pro, drag the file in, and pray the GPS didn't drift.")

# Fire in the hole
generate_tactical_kml('final_air3_targets.csv')