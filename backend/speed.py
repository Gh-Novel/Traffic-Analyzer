import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import os
import time
import base64
import json
import base64


def get_perspective_transform(frame, src_points):
    dst_points = np.float32([[0, 0], [500, 0], [500, 500], [0, 500]])
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    return matrix

def apply_perspective_transform(frame, matrix):
    return cv2.warpPerspective(frame, matrix, (500, 500))

def point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


async def process_speed_detection(video_path, roi_points, distance_meters):
    model = YOLO('yolov8l.pt')
    tracker = Tracker()
    vehicle_data = {}

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    perspective_matrix = get_perspective_transform(None, roi_points)

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        results = model(frame)
        detections = results[0].boxes.data.cpu().numpy()
        detected_objects = []
        for det in detections:
            x1, y1, x2, y2, conf, class_id = det
            if int(class_id) in [2, 3, 5, 7]:  # car, motorcycle, bus, truck
                detected_objects.append([int(x1), int(y1), int(x2), int(y2)])

        bbox_id = tracker.update(detected_objects)

        warped_frame = apply_perspective_transform(frame, perspective_matrix)

        # Create a copy of the frame for the transparent overlay
        overlay = frame.copy()
        
        # Draw filled purple ROI with 40% opacity
        cv2.fillPoly(overlay, [np.int32(roi_points)], (128, 0, 128))
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        # Draw ROI outline
        cv2.polylines(frame, [np.int32(roi_points)], True, (128, 0, 128), 2)

        for bbox in bbox_id:
            x1, y1, x2, y2, obj_id = bbox
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # Transform the center point to bird's eye view
            transformed_point = cv2.perspectiveTransform(np.array([[[cx, cy]]], dtype=np.float32), perspective_matrix)
            tx, ty = transformed_point[0][0]

            if obj_id not in vehicle_data:
                vehicle_data[obj_id] = {
                    'last_x': None,
                    'last_y': None,
                    'last_frame': None,
                    'speeds': [],
                    'avg_speed': None
                }

            if vehicle_data[obj_id]['last_frame'] is not None:
                if frame_count != vehicle_data[obj_id]['last_frame']:
                    dx = tx - vehicle_data[obj_id]['last_x']
                    dy = ty - vehicle_data[obj_id]['last_y']
                    distance = np.sqrt(dx**2 + dy**2)
                    time = (frame_count - vehicle_data[obj_id]['last_frame']) / fps
                    speed = (distance / 500) * (distance_meters / time) * 3.6  # km/h

                    vehicle_data[obj_id]['speeds'].append(speed)
                    if len(vehicle_data[obj_id]['speeds']) > 5:
                        vehicle_data[obj_id]['avg_speed'] = np.mean(vehicle_data[obj_id]['speeds'][-5:])
                    else:
                        vehicle_data[obj_id]['avg_speed'] = np.mean(vehicle_data[obj_id]['speeds'])

            vehicle_data[obj_id]['last_x'] = tx
            vehicle_data[obj_id]['last_y'] = ty
            vehicle_data[obj_id]['last_frame'] = frame_count

            # Display ID and average speed for all detected vehicles
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {obj_id}", (x1, y1 - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            if vehicle_data[obj_id]['avg_speed'] is not None:
                displayed_speed = 0 if vehicle_data[obj_id]['avg_speed'] < 5 else vehicle_data[obj_id]['avg_speed']
                speed_text = f"{displayed_speed:.2f} km/h"
                cv2.putText(frame, speed_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Yield the frame and vehicle data as a JSON object
        yield json.dumps({
            'frame': frame_base64,
            'vehicle_data': {k: {'avg_speed': v['avg_speed']} for k, v in vehicle_data.items() if v['avg_speed'] is not None}
        }) + '\n'

    cap.release()