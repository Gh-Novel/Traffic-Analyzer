import sys
import cv2
import numpy as np
import json
import base64

def process_video(video_path, roi_points):
    cap = cv2.VideoCapture(video_path)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert ROI points to numpy array
        roi_np = np.array([(point['x'], point['y']) for point in roi_points], np.int32)
        
        # Create a mask for the ROI
        mask = np.zeros(frame.shape[:2], np.uint8)
        cv2.fillPoly(mask, [roi_np], 255)

        # Apply the mask to the frame
        roi = cv2.bitwise_and(frame, frame, mask=mask)

        # Simple segmentation (you can replace this with your actual segmentation logic)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, segmented = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Convert segmented image to color for visualization
        segmented_color = cv2.cvtColor(segmented, cv2.COLOR_GRAY2BGR)
        
        # Combine the segmented ROI with the original frame
        result = frame.copy()
        result[mask > 0] = segmented_color[mask > 0]
        
        # Draw ROI outline
        cv2.polylines(result, [roi_np], True, (0, 255, 0), 2)
        
        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', result)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Create and print the JSON output
        output = json.dumps({
            'frame': frame_base64,
            'info': 'Segmentation processing'
        })
        print(output, flush=True)

    cap.release()

if __name__ == "__main__":
    if len(sys.argv) > 2:
        video_path = sys.argv[1]
        roi_points = json.loads(sys.argv[2])
        process_video(video_path, roi_points)
    else:
        print("Please provide a video file path and ROI points.")