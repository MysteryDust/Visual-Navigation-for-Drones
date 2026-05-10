import cv2
import pandas as pd
from ultralytics import YOLO
import os

def fuse_vision_and_telemetry(video_path, csv_path, srt_filename, model_path='best(yolov8n-visdrone).pt'):
    print(f"[INFO] Booting Sensor Fusion for {srt_filename}...")
    
    # 1. Load the Math Brain and isolate the specific flight
    df = pd.read_csv(csv_path)
    df_flight = df[df['source_file'] == srt_filename].copy()
    
    if df_flight.empty:
        return f"❌ ERROR: Could not find {srt_filename} in the CSV. Check your spelling."

    # 2. Load the Vision Brain
    try:
        model = YOLO(model_path)
    except Exception as e:
        return f"❌ Failed to load model. Error: {e}"

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return f"❌ Failed to open {video_path}."

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    center_x, center_y = width // 2, height // 2
    
    results_list = []
    
    print("[INFO] Initiating Real-Time Optical Navigation...")
    
    # Iterate through the math rows and the video frames simultaneously
    for _, row in df_flight.iterrows():
        success, frame = cap.read()
        if not success:
            print("⚠️ Video stream ended before telemetry data. This is normal due to dropped frames.")
            break
            
        # Run YOLO on the frame
        results = model(frame, conf=0.25, verbose=False)
        
        target_class = "Asphalt/Dirt"
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            # Is our static crosshair inside this detected object?
            if x1 <= center_x <= x2 and y1 <= center_y <= y2:
                cls_id = int(box.cls[0])
                target_class = model.names[cls_id]
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                break
        
        # Log the intelligence
        results_list.append({
            'timestamp': row['timestamp'],
            'target_lat': row['target_lat'],
            'target_lon': row['target_lon'],
            'detected_object': target_class
        })
        
        # HUD Visuals
        cv2.drawMarker(frame, (center_x, center_y), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
        cv2.putText(frame, f"GPS: {row['target_lat']:.5f}, {row['target_lon']:.5f}", 
                    (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"TARGET: {target_class.upper()}", 
                    (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        cv2.imshow("Optical HUD", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🛑 Manual Override. Aborting mission.")
            break
            
    cap.release()
    cv2.destroyAllWindows()
    
    # 3. Save the final payload
    output_df = pd.DataFrame(results_list)
    out_name = f"FUSED_{srt_filename.replace('.SRT', '.csv')}"
    output_df.to_csv(out_name, index=False)
    print(f"✅ Mission Accomplished. Target map saved to {out_name}")

# ==========================================
# EXECUTION COMMANDS
# Make sure your video file names match reality.
# ==========================================

## Run for Video 1
#fuse_vision_and_telemetry(
#    video_path='DJI_20260427152226_0017_D.mp4', 
#    csv_path='final_air3_targets.csv', 
##    srt_filename='DJI_20260427152226_0017_D.SRT'
#)

# Run for Video 2 
fuse_vision_and_telemetry(
    video_path='DJI_20260427152735_0019_D.mp4', 
    csv_path='final_air3_targets.csv', 
    srt_filename='DJI_20260427152735_0019_D.SRT'
)