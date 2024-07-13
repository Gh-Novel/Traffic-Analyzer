import React, { useRef, useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import DrawingCanvas from './DrawingCanvas';
import DrawingCanvas2 from './DrawingCanvas_w';
import DrawingCanvas_Speed from './DrawingCanvas_speed';
import './VideoSection.css';

function VideoSection({ snapshotUrl, videoUrl }) {
  const { mode } = useParams();
  const canvasRef = useRef();
  const [processing, setProcessing] = useState(false);
  const [processedImage, setProcessedImage] = useState(null);
  const [counts, setCounts] = useState([]);
  const [wrongWayCount, setWrongWayCount] = useState(0);
  const [vehicleData, setVehicleData] = useState({});
  const [buttonText, setButtonText] = useState('');
  const [endpoint, setEndpoint] = useState('');

  useEffect(() => {
    switch(mode) {
      case 'count':
        setButtonText('Process Count');
        setEndpoint('/Count');
        break;
      case 'wrong-lane':
        setButtonText('Process Wrong');
        setEndpoint('/Wrong');
        break;
      case 'speed':
        setButtonText('Process Speed');
        setEndpoint('/Speed');
        break;
      case 'segmentation':
        setButtonText('Process Speed');
        setEndpoint('/Segmentation');
        break;
      default:
        setButtonText('');
        setEndpoint('');
    }
  }, [mode]);

  const handleProcess = async () => {
    setProcessing(true);
    setProcessedImage(null);
    setCounts([]);
    setWrongWayCount(0);
    setVehicleData({});

    try {
      let data;
      if (mode === 'count') {
        data = { lines: canvasRef.current.getLines() };
      } else if (mode === 'wrong-lane' || mode === 'speed') {
        data = canvasRef.current.getData();
      }

      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to process: ${errorText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (line) {
            try {
              const data = JSON.parse(line);
              if (data.error) {
                throw new Error(data.error);
              }
              setProcessedImage(`data:image/jpeg;base64,${data.frame}`);
              if (mode === 'count') {
                setCounts(data.counts);
              } else if (mode === 'wrong-lane') {
                setWrongWayCount(data.wrong_way_count);
              } else if (mode === 'speed') {
                setVehicleData(data.vehicle_data);
              }
            } catch (parseError) {
              console.error('Error parsing JSON:', parseError);
              console.log('Problematic JSON string:', line);
            }
          }
        }
        
        buffer = lines[lines.length - 1];
      }
    } catch (error) {
      console.error('Error processing:', error);
      alert(`Failed to process: ${error.message}`);
    } finally {
      setProcessing(false);
    }
  };

  const renderCanvas = () => {
    switch (mode) {
      case 'count':
        return <DrawingCanvas ref={canvasRef} snapshotUrl={snapshotUrl} />;
      case 'wrong-lane':
        return <DrawingCanvas2 ref={canvasRef} snapshotUrl={snapshotUrl} />;
      case 'speed':
        return <DrawingCanvas_Speed ref={canvasRef} snapshotUrl={snapshotUrl} />;
      default:
        return <p>Please select a mode from the sidebar.</p>;
    }
  };

  return (
    <div className="video-section">
      <h2>{mode ? `${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode` : 'Video Processing'}</h2>
      {!processing && !processedImage && snapshotUrl && (
        <>
          {renderCanvas()}
          {buttonText && <button onClick={handleProcess}>{buttonText}</button>}
        </>
      )}
      {processing && <p>Processing... Please wait.</p>}
      {processedImage && (
        <div>
          <img src={processedImage} alt="Processed frame" style={{ width: '100%' }} />
          <div>
            {mode === 'count' && counts.map((count, index) => (
              <p key={index}>Line {index + 1} count: {count}</p>
            ))}
            {mode === 'wrong-lane' && (
              <p>Wrong Way Count: {wrongWayCount}</p>
            )}
            {mode === 'speed' && Object.entries(vehicleData).map(([vehicleId, data]) => (
              <p key={vehicleId}>Vehicle ID: {vehicleId}, Average Speed: {data.avg_speed?.toFixed(2) || 'N/A'} km/h</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default VideoSection;