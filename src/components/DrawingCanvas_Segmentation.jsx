import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';

const DrawingCanvas_Segmentation = forwardRef(({ snapshotUrl }, ref) => {
  const canvasRef = useRef(null);
  const backgroundImageRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [roi, setRoi] = useState([]);

  useImperativeHandle(ref, () => ({
    getData: () => ({ roi }),
    getLines: () => ({ roi })
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
    if (roi.length > 0) {
      context.beginPath();
      context.moveTo(roi[0].x, roi[0].y);
      for (let i = 1; i < roi.length; i++) {
        context.lineTo(roi[i].x, roi[i].y);
      }
      context.closePath();
      context.strokeStyle = 'yellow';
      context.lineWidth = 2;
      context.stroke();
    }
  };

  const handleMouseDown = (e) => {
    setIsDrawing(true);
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setRoi([...roi, { x, y }]);
  };

  const handleMouseMove = (e) => {
    if (!isDrawing) return;
    redrawAll();
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const handleMouseLeave = () => {
    setIsDrawing(false);
  };

  const handleClearROI = () => {
    setRoi([]);
    redrawAll();
  };

  return (
    <div>
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      ></canvas>
      <div className="controls">
        <button onClick={handleClearROI}>Clear ROI</button>
      </div>
    </div>
  );
});

export default DrawingCanvas_Segmentation;