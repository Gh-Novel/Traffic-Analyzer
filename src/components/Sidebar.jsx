// Sidebar.jsx

import React, { useState } from 'react';
import './Sidebar.css';
import { Link, useNavigate } from 'react-router-dom';

const Sidebar = ({ onVideoUpload, onIpSnapshot }) => {
  const [showIPOptions, setShowIPOptions] = useState(false);
  const [ipAddress, setIpAddress] = useState('');
  const [port, setPort] = useState('');
  const [feedStatus, setFeedStatus] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      onVideoUpload(file);
    }
  };

  const handleIPButtonClick = async (buttonId) => {
    setFeedStatus('');
    try {
      // First, get the snapshot
      const snapshotResponse = await fetch(`http://localhost:8000/get_snapshot?ip=${ipAddress}&port=${port}`);
      
      if (!snapshotResponse.ok) {
        throw new Error('Failed to fetch snapshot');
      }

      const snapshotBlob = await snapshotResponse.blob();
      const snapshotUrl = URL.createObjectURL(snapshotBlob);

      // Pass the snapshot URL to the parent component
      onIpSnapshot(snapshotUrl);

      // Then, start the stream
      const streamResponse = await fetch('http://localhost:8000/start_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ipAddress, port: port }),
      });

      if (streamResponse.ok) {
        setFeedStatus('Stream started successfully');
        navigate(`/video/${buttonId}?ip=${ipAddress}&port=${port}`);
      } else {
        setFeedStatus('Error: Unable to start stream');
      }
    } catch (error) {
      console.error('Error:', error);
      setFeedStatus(`Error: ${error.message}`);
    }
  };

  const buttons = [
    { name: 'Count', id: 'count' },
    { name: 'Wrong Lane', id: 'wrong-lane' },
    { name: 'Speed Detection', id: 'speed' },
    { name: 'Segmentation', id: 'segmentation' },
    { name: 'Track using IP', id: 'track-using-ip' },
    { name: 'All', id: 'all' }
  ];

  const ipButtons = [
    { name: 'Count IP', id: 'count_ip' },
    { name: 'Wrong Lane IP', id: 'wrong-lane_ip' },
    { name: 'Speed Detection IP', id: 'speed_ip' },
    { name: 'Segmentation IP', id: 'segmentation_ip' },
    { name: 'All IP', id: 'all_ip' }
  ];

  return (
    <div className="sidebar">
      <input type="file" onChange={handleFileChange} accept="video/*" />
      {buttons.map((button) => (
        <div key={button.id}>
          {button.id === 'track-using-ip' ? (
            <button 
              className="sidebar-button" 
              onClick={() => setShowIPOptions(!showIPOptions)}
            >
              {button.name}
            </button>
          ) : (
            <Link to={`/video/${button.id}`}>
              <button className="sidebar-button">{button.name}</button>
            </Link>
          )}
        </div>
      ))}
      {showIPOptions && (
        <div className="ip-options">
          <input 
            type="text" 
            placeholder="Enter IP address"
            value={ipAddress}
            onChange={(e) => setIpAddress(e.target.value)}
          />
          <input 
            type="text" 
            placeholder="Enter Port"
            value={port}
            onChange={(e) => setPort(e.target.value)}
          />
          {ipButtons.map((ipButton) => (
            <button 
              key={ipButton.id} 
              className="sidebar-button" 
              onClick={() => handleIPButtonClick(ipButton.id)}
            >
              {ipButton.name}
            </button>
          ))}
        </div>
      )}
      {feedStatus && <div>{feedStatus}</div>}
    </div>
  );
};

export default Sidebar;