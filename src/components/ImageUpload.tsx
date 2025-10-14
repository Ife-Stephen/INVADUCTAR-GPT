'use client'

import { useState } from 'react';

interface ImageUploadProps {
  onImageUpload: (file: File) => void;
}

export default function ImageUpload({ onImageUpload }: ImageUploadProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        onImageUpload(file);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onImageUpload(e.target.files[0]);
    }
  };

  return (
    <div style={{
      width: '100%',
      maxWidth: '400px',
      margin: '0 auto'
    }}>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? '#e53e3e' : '#0f3460'}`,
          borderRadius: '12px',
          padding: '32px 20px',
          textAlign: 'center',
          background: dragActive ? '#16213e' : '#1a1a2e',
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
      >
        <div style={{
          fontSize: '48px',
          marginBottom: '16px',
          color: dragActive ? '#e53e3e' : '#a0aec0'
        }}>
          🖼️
        </div>
        <h3 style={{
          fontSize: '18px',
          fontWeight: '600',
          marginBottom: '8px',
          color: 'white'
        }}>
          Upload Medical Image
        </h3>
        <p style={{
          fontSize: '14px',
          color: '#a0aec0',
          marginBottom: '20px',
          lineHeight: '1.5'
        }}>
          Drop your mammogram or breast imaging here, or click to browse
        </p>
        <label style={{
          display: 'inline-block',
          padding: '12px 24px',
          background: 'linear-gradient(135deg, #e53e3e, #c53030)',
          color: 'white',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '600',
          border: 'none'
        }}>
          Choose File
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </label>
        <div style={{
          fontSize: '12px',
          color: '#a0aec0',
          marginTop: '12px'
        }}>
          Supports: JPG, PNG, DICOM • Max 10MB
        </div>
      </div>
    </div>
  );
}