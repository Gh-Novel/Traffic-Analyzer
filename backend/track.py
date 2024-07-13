import cv2
import pandas as pd
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

class LineDetector:
    def __init__(self, start_x, start_y, end_x, end_y, offset=7):
        self.start_x = int(start_x)
        self.start_y = int(start_y)
        self.end_x = int(end_x)
        self.end_y = int(end_y)
        self.offset = offset
        self.counter = set()

    def is_crossing_line(self, cx, cy):
        if self.end_x != self.start_x:
            m = (self.end_y - self.start_y) / (self.end_x - self.start_x)
            b = self.start_y - m * self.start_x
            return abs(cy - (m * cx + b)) <= self.offset
        else:
            return abs(cx - self.start_x) <= self.offset

    def is_within_segment(self, cx, cy):
        if self.start_x <= self.end_x:
            if not (self.start_x <= cx <= self.end_x):
                return False
        else:
            if not (self.end_x <= cx <= self.start_x):
                return False

        if self.start_y <= self.end_y:
            return self.start_y <= cy <= self.end_y
        else:
            return self.end_y <= cy <= self.start_y

async def run_tracking(lines, video_path):
    try:
        model = YOLO('yolov9c.pt')
        class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
        vehicle_classes = ['bicycle', 'car', 'motorcycle', 'bus', 'truck']
        tracker = Tracker()

        line_detectors = [LineDetector(line['startX'], line['startY'], line['endX'], line['endY']) for line in lines]

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Error opening video file: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model.predict(frame)
            detections = results[0].boxes.data.detach().cpu().numpy()
            px = pd.DataFrame(detections).astype("float")
            detected_objects = []
            for _, row in px.iterrows():
                x1, y1, x2, y2, _, class_id = map(int, row)
                class_name = class_list[class_id]
                if class_name in vehicle_classes:
                    detected_objects.append([x1, y1, x2, y2])
                    # Draw the green bounding box for detected vehicles
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            bbox_id = tracker.update(detected_objects)

            for bbox in bbox_id:
                x1, y1, x2, y2, obj_id = bbox
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                for i, detector in enumerate(line_detectors):
                    if detector.is_crossing_line(cx, cy) and detector.is_within_segment(cx, cy):
                        detector.counter.add(obj_id)
                        cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                        cv2.putText(frame, str(obj_id), (cx, cy), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 2)

            for i, detector in enumerate(line_detectors):
                cv2.line(frame, (detector.start_x, detector.start_y), (detector.end_x, detector.end_y), (0, 0, 255), 3)
                cv2.putText(frame, f'Line {i+1}: {len(detector.counter)}', (10, 30 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Yield the frame as a JSON object
            frame_data = json.dumps({
                'frame': frame_base64,
                'counts': [len(detector.counter) for detector in line_detectors]
            })
            logger.info(f"Sending frame data: {frame_data[:100]}...")  # Log the first 100 characters
            yield frame_data + '\n'

            # Add a small delay to prevent blocking
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.error(f"Error in run_tracking: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        yield json.dumps({"error": str(e)}) + '\n'
    finally:
        if 'cap' in locals():
            cap.release()

async def process_lines(lines, video_path):
    try:
        logger.info(f"Starting video processing: {video_path}")
        async for frame_data in run_tracking(lines, video_path):
            yield frame_data
    except Exception as e:
        logger.error(f"Error in process_lines: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        yield json.dumps({"error": str(e)}) + '\n'

# Main function to test the code
async def main():
    video_path = "path/to/your/video.mp4"
    lines = [
        {"startX": 100, "startY": 200, "endX": 300, "endY": 200},
        {"startX": 400, "startY": 300, "endX": 600, "endY": 300}
    ]
    
    async for frame_data in process_lines(lines, video_path):
        print(frame_data)  # In a real application, you would send this data to the frontend

if __name__ == "__main__":
    asyncio.run(main())
