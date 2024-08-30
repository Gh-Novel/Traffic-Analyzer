import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import asyncio
import json
import base64

# Global variables
model = YOLO('yolov9c.pt')
tracker = Tracker()
current_lines = []

def update_lines(lines):
    global current_lines
    current_lines = lines

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

async def process_ip_stream(ip, port, lines):
    global current_lines
    current_lines = lines
    
    cap = cv2.VideoCapture(f"http://{ip}:{port}/video")
    
    if not cap.isOpened():
        raise Exception(f"Error opening video stream from {ip}:{port}")

    line_detectors = [LineDetector(line['startX'], line['startY'], line['endX'], line['endY']) for line in lines]

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame)
        detections = results[0].boxes.data.detach().cpu().numpy()

        detected_objects = []
        for row in detections:
            x1, y1, x2, y2, conf, class_id = row
            if conf > 0.5:  # Confidence threshold
                detected_objects.append([int(x1), int(y1), int(x2), int(y2)])

        bbox_id = tracker.update(detected_objects)

        for bbox in bbox_id:
            x1, y1, x2, y2, obj_id = bbox
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {obj_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            for i, detector in enumerate(line_detectors):
                if detector.is_crossing_line(cx, cy) and detector.is_within_segment(cx, cy):
                    detector.counter.add(obj_id)

        for i, detector in enumerate(line_detectors):
            cv2.line(frame, (detector.start_x, detector.start_y), (detector.end_x, detector.end_y), (0, 0, 255), 3)
            cv2.putText(frame, f'Line {i+1}: {len(detector.counter)}', (10, 30 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')

        data = {
            'frame': frame_base64,
            'counts': [len(detector.counter) for detector in line_detectors]
        }
        yield (json.dumps(data) + "\n").encode('utf-8')

        await asyncio.sleep(0.01)

    cap.release()

# You might want to add a main function if you want to test this script independently
if __name__ == "__main__":
    # Test code here
    pass