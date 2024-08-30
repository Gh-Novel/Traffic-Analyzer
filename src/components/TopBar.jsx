import React from 'react';
import './TopBar.css';

function TopBar() {
  const handleClick = (buttonName) => {
    alert(`You clicked ${buttonName}`);
  };

  return (
    <div className="top-bar">
      <button className="top-bar-button" onClick={() => handleClick('YOLO v8')}>YOLO v8</button>
      <button className="top-bar-button" onClick={() => handleClick('YOLO v9')}>YOLO v9</button>
      <button className="top-bar-button" onClick={() => handleClick('Tensorflow')}>Tensorflow</button>
    </div>
  );
}

export default TopBar;