from fastapi import FastAPI, File, UploadFile, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import cv2
import os
import logging
import traceback
import json
import numpy as np
import base64
import asyncio
import io
from pydantic import BaseModel
from typing import List
from track import process_lines
from Lane import process_wrong_lane
from speed import process_speed_detection
from track_ip import process_ip_stream, update_lines
from Lane_ip import process_wrong_lane_ip

import subprocess

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
f_name = None
stream_task = None

# Ensure the 'uploads' directory exists
os.makedirs("uploads", exist_ok=True)

STATIC_DIR = "."

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Line(BaseModel):
    startX: float
    startY: float
    endX: float
    endY: float

class StreamRequest(BaseModel):
    ip: str
    port: int
    lines: List[Line] = []
    
class IPPort(BaseModel):
    ip: str
    port: str

@app.get("/")
def read_index():
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

@app.get("/get_snapshot")
async def get_snapshot(ip: str, port: int):
    try:
        cap = cv2.VideoCapture(f"http://{ip}:{port}/video")
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=400, detail="Failed to capture snapshot")
        cap.release()
        
        _, buffer = cv2.imencode('.jpg', frame)
        return StreamingResponse(io.BytesIO(buffer.tobytes()), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class Line(BaseModel):
    startX: float
    startY: float
    endX: float
    endY: float

class StreamRequest(BaseModel):
    ip: str
    port: int
    lines: List[Line] = []

@app.post("/count_ip")
async def count_ip_stream(request: Request):
    try:
        data = await request.json()
        ip = data.get("ip")
        port = data.get("port")
        lines = data.get("lines", [])

        if not ip or not port or not lines:
            raise HTTPException(status_code=400, detail="IP, port, and lines are required")

        return StreamingResponse(process_ip_stream(ip, port, lines), media_type="application/x-ndjson")
    except Exception as e:
        logger.error(f"Error processing IP stream: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/Lane_ip")
async def process_wrong_lane_ip_endpoint(request: Request):
    try:
        data = await request.json()
        
        if not data.get("ip") or not data.get("port") or not data.get("roi") or not data.get("greenLine") or not data.get("redLine"):
            raise HTTPException(status_code=400, detail="Missing required data")

        return StreamingResponse(
            process_wrong_lane_ip(data),
            media_type="application/x-ndjson"
        )
    except Exception as e:
        logger.error(f"Error processing wrong lane IP: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    global f_name
    try:
        video_path = os.path.join("uploads", file.filename)
        
        with open(video_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Video '{file.filename}' uploaded successfully.")
        
        f_name = file.filename
        
        vidcap = cv2.VideoCapture(video_path)
        success, image = vidcap.read()
        if success:
            snapshot_filename = f"{file.filename}_snapshot.jpg"
            snapshot_path = os.path.join("uploads", snapshot_filename)
            cv2.imwrite(snapshot_path, image)
            logger.info(f"Snapshot for video '{file.filename}' saved successfully.")
            return {"info": f"Video '{file.filename}' saved at '{video_path}' and snapshot saved at '{snapshot_path}'", "snapshot": snapshot_filename}
        else:
            logger.error(f"Failed to read the video file '{file.filename}'.")
            raise HTTPException(status_code=400, detail="Failed to read video file")
    except Exception as e:
        logger.error(f"Error uploading video '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/Count")
async def process_multiple_lines(request: Request):
    global f_name
    try:
        data = await request.json()
        lines = data.get('lines', [])

        if not lines:
            raise HTTPException(status_code=400, detail="No lines provided")

        if f_name is None:
            raise HTTPException(status_code=400, detail="No video file uploaded")

        video_path = os.path.join("uploads", f_name)
        logger.info(f"Processing video: {video_path}")
        logger.info(f"Lines: {lines}")

        return StreamingResponse(process_lines(lines, video_path), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error processing lines: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/Wrong")
async def process_wrong_lane_endpoint(request: Request):
    global f_name
    try:
        data = await request.json()
        roi_points = data.get('roi', [])
        green_line = data.get('greenLine', {})
        red_line = data.get('redLine', {})

        if not roi_points or not green_line or not red_line:
            raise HTTPException(status_code=400, detail="Missing required data")

        if f_name is None:
            raise HTTPException(status_code=400, detail="No video file uploaded")

        video_path = os.path.join("uploads", f_name)
        logger.info(f"Processing video: {video_path}")
        logger.info(f"ROI: {roi_points}")
        logger.info(f"Green Line: {green_line}")
        logger.info(f"Red Line: {red_line}")

        return StreamingResponse(process_wrong_lane(roi_points, green_line, red_line, video_path), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error processing Wrong Lane: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/Speed")
async def process_speed(request: Request):
    global f_name
    try:
        data = await request.json()
        roi_points = data.get('roi', [])
        distance_meters = data.get('distance', 0)

        if not roi_points or not distance_meters:
            raise HTTPException(status_code=400, detail="Missing required data")

        if f_name is None:
            raise HTTPException(status_code=400, detail="No video file uploaded")

        video_path = os.path.join("uploads", f_name)
        logger.info(f"Processing video for speed detection: {video_path}")
        logger.info(f"ROI: {roi_points}")
        logger.info(f"Distance: {distance_meters} meters")

        roi_points_np = np.float32([[point['x'], point['y']] for point in roi_points])

        return StreamingResponse(process_speed_detection(video_path, roi_points_np, distance_meters), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error processing speed detection: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/Segmentation")
async def process_segmentation(request: Request):
    return await process_generic(request, "Segmentation")

@app.post("/All")
async def process_all(request: Request):
    return await process_generic(request, "All")

async def process_generic(request: Request, mode: str):
    global f_name
    try:
        data = await request.json()
        lines = data.get('lines', [])

        if not lines:
            raise HTTPException(status_code=400, detail="No lines provided")

        if f_name is None:
            raise HTTPException(status_code=400, detail="No video file uploaded")

        video_path = os.path.join("uploads", f_name)
        logger.info(f"Processing video: {video_path}")
        logger.info(f"Lines: {lines}")
        logger.info(f"Mode: {mode}")

        return StreamingResponse(process_lines(lines, video_path), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Error processing {mode}: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{file_path:path}")
def get_static_file(file_path: str):
    file_location = os.path.join(STATIC_DIR, file_path)
    if os.path.isfile(file_location):
        return FileResponse(file_location)
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            parsed_data = json.loads(data)
            await websocket.send_text(f"Received: {json.dumps(parsed_data)}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")


@app.post("/process_stream")
async def process_stream(request: StreamRequest):
    try:
        async def generate():
            try:
                async for frame_data in process_ip_stream(request.ip, request.port, request.lines):
                    yield (json.dumps(frame_data) + "\n").encode('utf-8')
            except Exception as e:
                yield json.dumps({"error": str(e)}).encode('utf-8')

        return StreamingResponse(generate(), media_type="application/x-ndjson")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/start_stream")
async def start_stream(ip_port: IPPort):
    try:
        url = f"http://{ip_port.ip}:{ip_port.port}/video"
        subprocess.Popen(['python', 'video_stream.py', url])
        return {"message": "Stream started successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/set_ip_port")
async def set_ip_port(ip_port: IPPort):
    try:
        url = f"http://{ip_port.ip}:{ip_port.port}/video"
        subprocess.Popen(['python', 'video_stream.py', url])
        return {"message": "IP and Port set successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/update_lines")
async def update_lines_endpoint(request: Request):
    try:
        data = await request.json()
        lines = data.get('lines', [])
        if not lines:
            raise HTTPException(status_code=400, detail="No lines provided")
        
        update_lines(lines)
        return {"message": "Lines updated successfully"}
    except Exception as e:
        logger.error(f"Error updating lines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
