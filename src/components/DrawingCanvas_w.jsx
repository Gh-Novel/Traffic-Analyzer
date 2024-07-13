import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';

const DrawingCanvas_w = forwardRef(({ snapshotUrl }, ref) => {
  const canvasRef = useRef(null);
  const backgroundImageRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [roi, setRoi] = useState([]);
  const [greenLine, setGreenLine] = useState({ start: null, end: null });
  const [redLine, setRedLine] = useState({ start: null, end: null });
  const [drawingMode, setDrawingMode] = useState('roi');

  useImperativeHandle(ref, () => ({
    getData: () => ({ roi, greenLine, redLine }),
    getLines: () => ({
      roi,
      greenLine,
      redLine
    })
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

    // Draw green line
    if (greenLine.start && greenLine.end) {
      context.beginPath();
      context.moveTo(greenLine.start.x, greenLine.start.y);
      context.lineTo(greenLine.end.x, greenLine.end.y);
      context.strokeStyle = 'green';
      context.lineWidth = 2;
      context.stroke();
    }

    // Draw red line
    if (redLine.start && redLine.end) {
      context.beginPath();
      context.moveTo(redLine.start.x, redLine.start.y);
      context.lineTo(redLine.end.x, redLine.end.y);
      context.strokeStyle = 'red';
      context.lineWidth = 2;
      context.stroke();
    }
  };

  const handleMouseDown = (e) => {
    setIsDrawing(true);
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (drawingMode === 'roi') {
      setRoi([...roi, { x, y }]);
    } else if (drawingMode === 'green') {
      setGreenLine({ start: { x, y }, end: null });
    } else if (drawingMode === 'red') {
      setRedLine({ start: { x, y }, end: null });
    }
  };

  const handleMouseMove = (e) => {
    if (!isDrawing) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (drawingMode === 'green' && greenLine.start) {
      setGreenLine({ ...greenLine, end: { x, y } });
    } else if (drawingMode === 'red' && redLine.start) {
      setRedLine({ ...redLine, end: { x, y } });
    }

    redrawAll();
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
    if (drawingMode === 'green' || drawingMode === 'red') {
      setDrawingMode('roi');
    }
  };

  const handleMouseLeave = () => {
    setIsDrawing(false);
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
        <button onClick={() => setDrawingMode('roi')}>Draw ROI</button>
        <button onClick={() => setDrawingMode('green')}>Draw Green Line</button>
        <button onClick={() => setDrawingMode('red')}>Draw Red Line</button>
        <button onClick={() => { setRoi([]); setGreenLine({ start: null, end: null }); setRedLine({ start: null, end: null }); redrawAll(); }}>Clear All</button>
      </div>
    </div>
  );
});

export default DrawingCanvas_w;
