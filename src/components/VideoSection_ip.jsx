import React, { useState } from 'react';
import DC_ip from './DC_ip';
import './VideoSection_ip.css';

function VideoSection_ip({ ipAddress, port }) {
  const [snapshot, setSnapshot] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedImage, setProcessedImage] = useState(null);
  const [counts, setCounts] = useState([]);
  const [error, setError] = useState(null);

  const startStream = async () => {
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/start_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ipAddress, port: port }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSnapshot(`http://localhost:8000/${data.snapshot_path}`);
      } else {
        setError('Error: Unable to start stream');
      }
    } catch (error) {
      setError('Error: Unable to connect to server');
    }
  };

  const startProcessing = async () => {
    setIsProcessing(true);
    setError(null);
    const lines = []; // Get lines from DC_ip component
    try {
      const response = await fetch('http://localhost:8000/process_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ipAddress, port: port, lines: lines }),
      });
      
      if (response.ok) {
        const reader = response.body.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const data = JSON.parse(new TextDecoder().decode(value));
          setProcessedImage(`data:image/jpeg;base64,${data.frame}`);
          setCounts(data.counts);
        }
      } else {
        setError('Failed to process stream');
      }
    } catch (error) {
      setError('Error connecting to server');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div>
      <button onClick={startStream}>Start Stream</button>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {snapshot && (
        <div>
          <DC_ip imageUrl={snapshot} />
          <button onClick={startProcessing} disabled={isProcessing}>
            {isProcessing ? 'Processing...' : 'Start Processing'}
          </button>
        </div>
      )}
      {processedImage && (
        <div>
          <img src={processedImage} alt="Processed frame" />
          {counts.map((count, index) => (
            <p key={index}>Line {index + 1} count: {count}</p>
          ))}
        </div>
      )}
    </div>
  );
}

export default VideoSection_ip;