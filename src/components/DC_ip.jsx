import React, { useEffect, useState, forwardRef, useImperativeHandle } from 'react';

const DC_ip = forwardRef(({ imageUrl, ip, port }, ref) => {
  const [lines, setLines] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const canvasRef = React.useRef(null);

  useImperativeHandle(ref, () => ({
    getLines: () => lines
  }));

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      redrawLines();
    };
    img.src = imageUrl;
  }, [imageUrl]);

  const redrawLines = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const img = new Image();
    img.onload = () => {
      ctx.drawImage(img, 0, 0);
      lines.forEach((line, index) => {
        ctx.beginPath();
        ctx.moveTo(line.startX, line.startY);
        ctx.lineTo(line.endX, line.endY);
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Draw line number
        const midX = (line.startX + line.endX) / 2;
        const midY = (line.startY + line.endY) / 2;
        ctx.fillStyle = 'red';
        ctx.font = '16px Arial';
        ctx.fillText(`${index + 1}`, midX, midY);
      });
    };
    img.src = imageUrl;
  };

  const handleMouseDown = (e) => {
    setIsDrawing(true);
    const { offsetX, offsetY } = e.nativeEvent;
    setLines([...lines, { startX: offsetX, startY: offsetY, endX: offsetX, endY: offsetY }]);
  };

  const handleMouseMove = (e) => {
    if (!isDrawing) return;
    const { offsetX, offsetY } = e.nativeEvent;
    setLines(lines.map((line, index) =>
      index === lines.length - 1 ? { ...line, endX: offsetX, endY: offsetY } : line
    ));
    redrawLines();
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const handleProcessClick = async () => {
    try {
      const response = await fetch('http://localhost:8000/count_ip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, port, lines })
      });
      if (response.ok) {
        console.log('Lines sent successfully');
      } else {
        console.error('Failed to send lines');
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      />
      <button onClick={handleProcessClick}>Process Count (IP)</button>
    </div>
  );
});

export default DC_ip;
