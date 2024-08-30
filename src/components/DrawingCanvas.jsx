import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';

const DrawingCanvas = forwardRef(({ snapshotUrl }, ref) => {
  const canvasRef = useRef(null);
  const backgroundImageRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [lines, setLines] = useState([]);
  const [selectedColor, setSelectedColor] = useState('#000000');
  const [size, setSize] = useState(5);

  useImperativeHandle(ref, () => ({
    getLines: () => lines
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

  const drawLine = (context, line, index) => {
    context.beginPath();
    context.moveTo(line.startX, line.startY);
    context.lineTo(line.endX, line.endY);
    context.strokeStyle = line.color;
    context.lineWidth = line.size;
    context.stroke();

    // Calculate midpoint
    const midX = (line.startX + line.endX) / 2;
    const midY = (line.startY + line.endY) / 2;

    // Draw box
    context.fillStyle = 'white';
    context.fillRect(midX - 10, midY - 10, 20, 20);

    // Draw border
    context.strokeStyle = 'black';
    context.lineWidth = 1;
    context.strokeRect(midX - 10, midY - 10, 20, 20);

    // Draw number
    context.fillStyle = 'black';
    context.font = '12px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(index + 1, midX, midY);
  };

  const redrawAll = () => {
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);

    if (backgroundImageRef.current) {
      context.drawImage(backgroundImageRef.current, 0, 0);
    }

    lines.forEach((line, index) => drawLine(context, line, index));
  };

  const handleMouseDown = (e) => {
    setIsDrawing(true);
    const rect = canvasRef.current.getBoundingClientRect();
    const startX = e.clientX - rect.left;
    const startY = e.clientY - rect.top;
    const newLine = { startX, startY, endX: startX, endY: startY, color: selectedColor, size };
    setLines(prevLines => [...prevLines, newLine]);
  };

  const handleMouseMove = (e) => {
    if (!isDrawing) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;

    setLines(prevLines => {
      const updatedLines = [...prevLines];
      const currentLine = updatedLines[updatedLines.length - 1];
      currentLine.endX = endX;
      currentLine.endY = endY;
      return updatedLines;
    });

    redrawAll();
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const handleMouseLeave = () => {
    setIsDrawing(false);
  };

  const handleProcessClick = async () => {
    try {
      const linesToSend = lines.map(line => ({
        startX: line.startX,
        startY: line.startY,
        endX: line.endX,
        endY: line.endY,
        color: line.color,
        size: line.size
      }));
  
      // Update the URL to point to your backend server
      const response = await fetch('http://localhost:8000/Count', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ lines: linesToSend })
      });
  
      if (!response.ok) {
        throw new Error('Failed to process lines');
      }
  
      // Optionally handle response
      const result = await response.json();
      console.log('Processing result:', result);
    } catch (error) {
      console.error('Error processing lines:', error.message);
    }
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
        <input
          type="color"
          value={selectedColor}
          onChange={(e) => setSelectedColor(e.target.value)}
        />
        <input
          type="range"
          min="1"
          max="20"
          value={size}
          onChange={(e) => setSize(parseInt(e.target.value, 10))}
        />
        <button onClick={handleProcessClick}>Process</button>
      </div>
    </div>
  );
});

export default DrawingCanvas;