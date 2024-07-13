import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';

const DrawingCanvas_Speed = forwardRef(({ snapshotUrl }, ref) => {
  const canvasRef = useRef(null);
  const backgroundImageRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [roi, setRoi] = useState([]);
  const [distance, setDistance] = useState('');

  useImperativeHandle(ref, () => ({
    getData: () => ({ roi, distance: parseFloat(distance) }),
  }));

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (snapshotUrl) {
      const image = new Image();
      image.src = snapshotUrl;
      image.onload = () => {
        canvas.width = image.width;
        canvas.height = image.height;
        context.drawImage(image, 0, 0);
        backgroundImageRef.current = image;
        redrawAll();
      };
    }
  }, [snapshotUrl]);

  const redrawAll = () => {
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    
    if (backgroundImageRef.current) {
      context.drawImage(backgroundImageRef.current, 0, 0);
    }
    
    // Draw ROI
    if (roi.length === 4) {
      context.beginPath();
      context.moveTo(roi[0].x, roi[0].y);
      for (let i = 1; i < roi.length; i++) {
        context.lineTo(roi[i].x, roi[i].y);
      }
      context.closePath();
      context.strokeStyle = 'purple';
      context.lineWidth = 2;
      context.stroke();
    }
  };

  const handleMouseDown = (e) => {
    if (roi.length < 4) {
      setIsDrawing(true);
      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setRoi([...roi, { x, y }]);
    }
  };

  const handleMouseMove = (e) => {
    if (isDrawing && roi.length < 4) {
      redrawAll();
    }
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
    if (roi.length === 4) {
      redrawAll();
    }
  };

  const handleDistanceChange = (e) => {
    setDistance(e.target.value);
  };

  const handleClear = () => {
    setRoi([]);
    setDistance('');
    redrawAll();
  };

  return (
    <div>
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      ></canvas>
      <div className="controls">
        <input 
          type="number" 
          value={distance} 
          onChange={handleDistanceChange} 
          placeholder="Enter distance in meters" 
        />
        <button onClick={handleClear}>Clear</button>
      </div>
    </div>
  );
});

export default DrawingCanvas_Speed;