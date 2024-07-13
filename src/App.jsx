import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import TopBar from './components/TopBar';
import Sidebar from './components/Sidebar';
import VideoSection from './components/VideoSection';
import './App.css';

function App() {
  const [snapshotUrl, setSnapshotUrl] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  const handleVideoUpload = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/upload_video', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload video');
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }

      alert('Video uploaded successfully!');
      setSnapshotUrl(`http://localhost:8000/uploads/${data.snapshot}`);
      setVideoUrl(`http://localhost:8000/uploads/${file.name}`);
    } catch (error) {
      console.error('Error uploading video:', error);
      alert('Failed to upload video');
    }
  };

  return (
    <Router>
      <div className="container">
        <TopBar />
        <div className="main-content">
          <Sidebar onVideoUpload={handleVideoUpload} />
          <Routes>
            <Route 
              path="/" 
              element={<VideoSection snapshotUrl={snapshotUrl} videoUrl={videoUrl} />} 
            />
            <Route 
              path="/video/:mode" 
              element={<VideoSection snapshotUrl={snapshotUrl} videoUrl={videoUrl} />} 
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;