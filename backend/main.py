from fastapi import FastAPI, File, UploadFile, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import cv2
import os
import logging
import traceback
import json
import numpy as np
import base64
import asyncio
from track import process_lines
from Lane import process_wrong_lane
from speed import process_speed_detection

app = FastAPI()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Initialize the variable to hold the filename globally
f_name = None

@app.get("/")
def read_index():
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    global f_name
    try:
        video_path = os.path.join("uploads", file.filename)
        
        # Save the uploaded video file
        with open(video_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Video '{file.filename}' uploaded successfully.")
        
        # Store the filename in a variable
        f_name = file.filename
        
        # Take a snapshot of the first frame using OpenCV
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

        # Convert roi_points to the format expected by process_speed_detection
        roi_points_np = np.float32([[point['x'], point['y']] for point in roi_points])

        # Use the process_speed_detection function
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

        # Here you would implement the specific processing for each mode
        # For now, we'll just use the existing process_lines function
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
            # Process the received data
            # For example, you could parse it as JSON
            parsed_data = json.loads(data)
            
            # Do something with the data
            # For this example, we'll just echo it back
            await websocket.send_text(f"Received: {json.dumps(parsed_data)}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)