// VideoSection.jsx

import React, { useRef, useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import DrawingCanvas from './DrawingCanvas';
import DrawingCanvas2 from './DrawingCanvas_w';
import DrawingCanvas_Speed from './DrawingCanvas_speed';
import DC_ip from './DC_ip';
import DrawingCanvas_w_ip from './DrawingCanvas_w_ip';
import './VideoSection.css';

function VideoSection({ snapshotUrl, videoUrl }) {
  const { mode } = useParams();
  const location = useLocation();
  const canvasRef = useRef();
  const [processing, setProcessing] = useState(false);
  const [processedImage, setProcessedImage] = useState(null);
  const [counts, setCounts] = useState([]);
  const [wrongWayCount, setWrongWayCount] = useState(0);
  const [vehicleData, setVehicleData] = useState({});
  const [buttonText, setButtonText] = useState('');
  const [endpoint, setEndpoint] = useState('');
  const [ipSnapshot, setIpSnapshot] = useState(null);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const ip = searchParams.get('ip');
    const port = searchParams.get('port');

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
        setButtonText('Process Segmentation');
        setEndpoint('/Segmentation');
        break;
      case 'count_ip':
        setButtonText('Process Count (IP)');
        setEndpoint('/count_ip');
        if (ip && port) {
          fetchIpSnapshot(ip, port);
        }
        break;
      case 'wrong-lane_ip':
        setButtonText('Process Wrong Lane (IP)');
        setEndpoint('/Lane_ip');
        if (ip && port) {
          fetchIpSnapshot(ip, port);
        }
        break;
      default:
        setButtonText('');
        setEndpoint('');
    }
  }, [mode, location.search]);

  const fetchIpSnapshot = async (ip, port) => {
    try {
      const response = await fetch(`http://localhost:8000/get_snapshot?ip=${ip}&port=${port}`);
      if (response.ok) {
        const imageBlob = await response.blob();
        const imageUrl = URL.createObjectURL(imageBlob);
        setIpSnapshot(imageUrl);
      } else {
        throw new Error('Failed to fetch snapshot');
      }
    } catch (error) {
      console.error('Error fetching IP snapshot:', error);
      alert('Failed to fetch IP snapshot. Please check the IP and port.');
    }
  };

  const handleProcess = async () => {
    setProcessing(true);
    setProcessedImage(null);
    setCounts([]);
    setWrongWayCount(0);
    setVehicleData({});

    try {
      let data;
      if (mode === 'count' || mode === 'count_ip') {
        data = { lines: canvasRef.current.getLines() };
      } else if (mode === 'wrong-lane' || mode === 'speed' || mode === 'wrong-lane_ip') {
        data = canvasRef.current.getData();
      }

      if (mode === 'count_ip' || mode === 'wrong-lane_ip') {
        const searchParams = new URLSearchParams(location.search);
        data.ip = searchParams.get('ip');
        data.port = searchParams.get('port');
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
              if (mode === 'count' || mode === 'count_ip') {
                setCounts(data.counts);
              } else if (mode === 'wrong-lane' || mode === 'wrong-lane_ip') {
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
    const currentSnapshot = mode === 'count_ip' || mode === 'wrong-lane_ip' ? ipSnapshot : snapshotUrl;
    switch (mode) {
      case 'count':
        return <DrawingCanvas ref={canvasRef} snapshotUrl={currentSnapshot} />;
      case 'count_ip':
        return <DC_ip ref={canvasRef} imageUrl={currentSnapshot} />;
      case 'wrong-lane':
        return <DrawingCanvas2 ref={canvasRef} snapshotUrl={currentSnapshot} />;
      case 'wrong-lane_ip':
        return <DrawingCanvas_w_ip ref={canvasRef} imageUrl={currentSnapshot} />;
      case 'speed':
        return <DrawingCanvas_Speed ref={canvasRef} snapshotUrl={currentSnapshot} />;
      default:
        return <p>Please select a mode from the sidebar.</p>;
    }
  };

  return (
    <div className="video-section">
      <h2>{mode ? `${mode.charAt(0).toUpperCase() + mode.slice(1).replace('_', ' ')} Mode` : 'Video Processing'}</h2>
      {!processing && !processedImage && (snapshotUrl || ipSnapshot) && (
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
            {(mode === 'count' || mode === 'count_ip') && counts.map((count, index) => (
              <p key={index}>Line {index + 1} count: {count}</p>
            ))}
            {(mode === 'wrong-lane' || mode === 'wrong-lane_ip') && (
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