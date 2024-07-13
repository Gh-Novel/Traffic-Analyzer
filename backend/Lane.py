import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import os
import json
import base64
import logging
import traceback
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if np.isscalar(y) and np.isscalar(p1y) and np.isscalar(p2y):
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
        p1x, p1y = p2x, p2y
    return inside

async def run_tracking(roi_points, green_line, red_line, video_path, offset=7):
    model = YOLO('yolov8l.pt')
    class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
    tracker = Tracker()
    vehicle_states = {}
    wrong_way_count = 0

    # Convert roi_points to a list of tuples
    roi_points = [(int(point['x']), int(point['y'])) for point in roi_points]

    # Convert green_line and red_line to integer coordinates
    green_line = {
        'start': {'x': int(green_line['start']['x']), 'y': int(green_line['start']['y'])},
        'end': {'x': int(green_line['end']['x']), 'y': int(green_line['end']['y'])}
    }
    red_line = {
        'start': {'x': int(red_line['start']['x']), 'y': int(red_line['start']['y'])},
        'end': {'x': int(red_line['end']['x']), 'y': int(red_line['end']['y'])}
    }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video file at path {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        detections = results[0].boxes.data.cpu().numpy()
        detected_objects = []
        
        for detection in detections:
            x1, y1, x2, y2, conf, class_id = detection
            class_id = int(class_id)
            if class_list[class_id] in ['car', 'truck', 'bus', 'motorcycle']:
                cx, cy = int((x1 + x2) // 2), int((y1 + y2) // 2)
                if point_inside_polygon(cx, cy, roi_points):
                    detected_objects.append([int(x1), int(y1), int(x2), int(y2)])

        bbox_id = tracker.update(detected_objects)

        for bbox in bbox_id:
            x1, y1, x2, y2, obj_id = bbox
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if obj_id not in vehicle_states:
                vehicle_states[obj_id] = {'touched_green': False, 'touched_red': False, 'wrong_way': False}

            # Check if vehicle touches the green line
            if green_line['start']['y'] - offset < cy < green_line['start']['y'] + offset and green_line['start']['x'] < cx < green_line['end']['x']:
                vehicle_states[obj_id]['touched_green'] = True

            # Check if vehicle touches the red line
            if red_line['start']['y'] - offset < cy < red_line['start']['y'] + offset and red_line['start']['x'] < cx < red_line['end']['x']:
                if not vehicle_states[obj_id]['touched_green']:
                    vehicle_states[obj_id]['wrong_way'] = True
                    if not vehicle_states[obj_id]['touched_red']:
                        wrong_way_count += 1
                vehicle_states[obj_id]['touched_red'] = True

            # Draw bounding box
            color = (0, 255, 0)  # Default green
            if vehicle_states[obj_id]['wrong_way']:
                color = (0, 0, 255)  # Red for wrong way

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, str(obj_id), (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Draw ROI
        cv2.polylines(frame, [np.array(roi_points, np.int32)], isClosed=True, color=(255, 255, 0), thickness=2)

        # Draw lines
        cv2.line(frame, (green_line['start']['x'], green_line['start']['y']), (green_line['end']['x'], green_line['end']['y']), (0, 255, 0), 3)
        cv2.line(frame, (red_line['start']['x'], red_line['start']['y']), (red_line['end']['x'], red_line['end']['y']), (0, 0, 255), 3)

        # Display counts
        cv2.putText(frame, f'Wrong Way: {wrong_way_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Yield the frame as a JSON object
        frame_data = json.dumps({
            'frame': frame_base64,
            'wrong_way_count': wrong_way_count
        })
        yield frame_data + '\n'

        # Add a small delay to prevent blocking
        await asyncio.sleep(0.01)

    cap.release()

async def process_wrong_lane(roi_points, green_line, red_line, video_path):
    try:
        logger.info(f"Starting wrong lane detection: {video_path}")
        logger.info(f"ROI points: {roi_points}")
        logger.info(f"Green line: {green_line}")
        logger.info(f"Red line: {red_line}")
        
        async for frame_data in run_tracking(roi_points, green_line, red_line, video_path):
            yield frame_data
    except Exception as e:
        logger.error(f"Error in process_wrong_lane: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        yield json.dumps({"error": str(e)}) + '\n'

# Main function to test the code
async def main():
    video_path = "path/to/your/video.mp4"
    roi_points = [{'x': 100, 'y': 100}, {'x': 300, 'y': 100}, {'x': 300, 'y': 300}, {'x': 100, 'y': 300}]
    green_line = {"start": {"x": 100, "y": 200}, "end": {"x": 300, "y": 200}}
    red_line = {"start": {"x": 100, "y": 250}, "end": {"x": 300, "y": 250}}
    
    async for frame_data in process_wrong_lane(roi_points, green_line, red_line, video_path):
        print(frame_data)  # In a real application, you would send this data to the frontend

if __name__ == "__main__":
    asyncio.run(main())