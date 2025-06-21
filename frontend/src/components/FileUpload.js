import React, { useState, useCallback } from 'react';
import { Upload, File } from 'lucide-react';
import './styledcomponents.css';

export default function FileUpload({ label, onFileSelect }) {
    const [selectedFileName, setSelectedFileName] = useState('');
    const [isDragging, setIsDragging] = useState(false);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setSelectedFileName(file.name);
            onFileSelect(file);
        }
    };

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDragIn = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragOut = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        
        const file = e.dataTransfer.files[0];
        if (file) {
            setSelectedFileName(file.name);
            onFileSelect(file);
        }
    }, [onFileSelect]);

    return (
        <div className="file-upload-container">
            <div 
                className={`file-upload-area ${isDragging ? 'dragging' : ''}`}
                onDragEnter={handleDragIn}
                onDragLeave={handleDragOut}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <input 
                    type="file" 
                    className="file-input"
                    onChange={handleFileChange}
                    id="file-input"
                />
                <label htmlFor="file-input" className="file-label">
                    {typeof label === 'string' ? (
                        <>
                            <Upload size={32} className="upload-icon" />
                            <span>{label}</span>
                        </>
                    ) : (
                        label
                    )}
                </label>
            </div>
        </div>
    );
}