import React from 'react';
import './Sidebar.css';
import { Link } from 'react-router-dom';

const Sidebar = ({ onVideoUpload }) => {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      onVideoUpload(file);
    }
  };

  const buttons = [
    { name: 'Count', id: 'count' },
    { name: 'Wrong Lane', id: 'wrong-lane' },
    { name: 'Speed Detection', id: 'speed' },
    { name: 'Segmetationn', id: 'segmentation' },
    { name: 'Track using IP', id: 'track-using-ip' },
    { name: 'All', id: 'all' }
  ];

  return (
    <div className="sidebar">
      <input type="file" onChange={handleFileChange} accept="video/*" />
      {buttons.map((button) => (
        <Link key={button.id} to={`/video/${button.id}`}>
          <button className="sidebar-button">{button.name}</button>
        </Link>
      ))}
    </div>
  );
};

export default Sidebar;
