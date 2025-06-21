import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import { Upload, Edit2, Save, RefreshCw, ArrowRight, ChevronDown, Check, X, Repeat, Trash2, Camera, Smartphone, Monitor, RotateCcw } from 'lucide-react';
import './UploadID.css';

function UploadID() {
  const navigate = useNavigate();
  const location = useLocation();
  const [files, setFiles] = useState([]);
  const [filePreviews, setFilePreviews] = useState([]);
  const [extractedData, setExtractedData] = useState({});
  const [editableData, setEditableData] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showScrollIndicator, setShowScrollIndicator] = useState(false);
  const extractedDataRef = useRef(null);
  const [showCamera, setShowCamera] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [currentFacingMode, setCurrentFacingMode] = useState(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [loading, setLoading] = useState(true);

  const [keyOrder, setKeyOrder] = useState([
          "Name",
          "First Name",
          "Last Name",
          "Date of Birth",
          "Phone Number",
          "Aadhaar Number",
          "Gender",
          "PAN Number",
          "VID Number",
          "Address"
      ]);
  useEffect(() => {
    // Hide preloader after 5 seconds
    const timer = setTimeout(() => {
      setLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  // Retrieve state from location if available
  useEffect(() => {
    if (location.state) {
      const { idFiles, extractedData } = location.state;
      setFiles(idFiles);
      setExtractedData(extractedData);
      setEditableData(extractedData);
      setFilePreviews(idFiles.map(file => URL.createObjectURL(file)));
      // Update key order based on the order from the backend, if available
      const receivedKeys = Object.keys(extractedData);
      if (receivedKeys.length > 0) {
          setKeyOrder(receivedKeys);
      }
    }
  }, [location.state]);

  // Detect if device is mobile
  useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i;
      setIsMobile(mobileRegex.test(userAgent));
    };
    
    checkMobile();
  }, []);

  // Handle camera initialization after video element is mounted
  useEffect(() => {
    if (showCamera && videoRef.current && !isCameraReady) {
      initializeCamera();
    }
  }, [showCamera]);

  const initializeCamera = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera API is not supported in this browser');
      }

      // Set initial facing mode based on device type
      const facingMode = isMobile ? 'environment' : 'user';

      const constraints = {
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setCurrentFacingMode(facingMode);
        setIsCameraReady(true);
        
        // Ensure video plays after loading
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play().catch(e => console.error('Error playing video:', e));
        };
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError(getErrorMessage(err));
      setShowCamera(false);
    }
  };

  const getErrorMessage = (error) => {
    if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
      return 'Camera access denied. Please grant camera permissions and try again.';
    } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
      return 'No camera found on your device.';
    } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
      return 'Camera is in use by another application.';
    } else {
      return `Failed to access camera: ${error.message}`;
    }
  };

  const toggleCamera = () => {
    if (showCamera) {
      stopCamera();
    } else {
      setShowCamera(true);
    }
  };

  const switchCamera = async () => {
    const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    stopCamera();
    
    // Short delay to ensure previous stream is properly stopped
    setTimeout(() => {
      setShowCamera(true);
      setCurrentFacingMode(newFacingMode);
    }, 100);
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setShowCamera(false);
    setIsCameraReady(false);
    setCurrentFacingMode(null);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const capturePhoto = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoRef.current, 0, 0);

      canvas.toBlob((blob) => {
        const file = new File([blob], `camera-capture-${Date.now()}.jpg`, { type: 'image/jpeg' });
        setFiles(prevFiles => [...prevFiles, file]);
        setFilePreviews(prevPreviews => [...prevPreviews, URL.createObjectURL(blob)]);
      }, 'image/jpeg', 0.95);

      stopCamera();
    }
  };

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
    if (!isEditing) {
      // Reset editable data to current extracted data when starting edit
      setEditableData({ ...extractedData });
    }
  };

  const handleInlineEdit = (key, value) => {
    setEditableData(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(prevFiles => [...prevFiles, ...selectedFiles]);
    setFilePreviews(prevPreviews => [...prevPreviews, ...selectedFiles.map(file => URL.createObjectURL(file))]);
  };

  const scrollToExtractedData = () => {
    extractedDataRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select at least one ID document');
      return;
    }

    setIsLoading(true);
    setError(null);
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const response = await axios.post('http://localhost:5000/upload-id', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      const newExtractedData = response.data.extracted_data;
      setExtractedData(prevData => ({ ...prevData, ...newExtractedData }));
      setEditableData(prevData => ({ ...prevData, ...newExtractedData }));
      setShowScrollIndicator(true);
      // Short delay to ensure the data is rendered before scrolling
      setTimeout(scrollToExtractedData, 500);
    } catch (error) {
      console.error('Error uploading files:', error);
      setError('Failed to upload files. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditChange = (event) => {
    const { name, value } = event.target;
    setEditableData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleDeleteFile = (indexToDelete) => {
    setFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToDelete));
    setFilePreviews(prevPreviews => prevPreviews.filter((_, index) => index !== indexToDelete));

    // If we're deleting the last file, also clear the extracted data
    if (files.length === 1) {
      setExtractedData({});
      setEditableData({});
    }
  };

  const handleUpdateData = async () => {
    try {
      setIsLoading(true);
      await axios.post('http://localhost:5000/update-data', editableData, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      setExtractedData(editableData);
      setIsEditing(false);
      setError(null);
    } catch (error) {
      console.error('Error updating data:', error);
      setError('Failed to update data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditableData({ ...extractedData });
  };

  const handleUploadForm = () => {
    navigate('/upload-form', { state: { idFiles: files, extractedData } });
  };

  const handleSwapNames = () => {
    let Name = editableData['Name'] || '';
    let firstName = editableData['First Name'] || '';
    let lastName = editableData['Last Name'] || '';

    if (Name) {
      let nameParts = Name.split(' ');
      if (nameParts.length > 1) {
        setEditableData({
          ...editableData,
          'First Name': nameParts.slice(1).join(' '),
          'Last Name': nameParts[0],
        });
      } else {
        setEditableData({
          ...editableData,
          'First Name': '',
          'Last Name': firstName,
        });
      }
    }
  };

  const renderExtractedData = () => {
    if (!extractedData || Object.keys(extractedData).length === 0) {
      return <p>No data extracted yet.</p>;
    }

    return (
      <div className="data-card">
        {keyOrder.map((key) => (
          <div key={key} className="data-row">
            <span className="data-label">{key}:</span>
            {isEditing ? (
              <div className="editable-value">
                <input
                  type="text"
                  value={editableData[key] || ''}
                  onChange={(e) => handleInlineEdit(key, e.target.value)}
                  className="inline-edit-input"
                  autoFocus={key === keyOrder[0]}
                />
                <Edit2 size={16} className="edit-indicator" />
                {key === 'Last Name' && (
                  <button
                    onClick={handleSwapNames}
                    className="swap-names-button"
                    title="Correct First and Last Names"
                  >
                    <Repeat size={16} />
                  </button>
                )}
              </div>
            ) : (
              <span className="data-value">{extractedData[key] || ''}</span>
            )}
          </div>
        ))}
      </div>
    );
  };
  return (
    <>
    <div className={`preloader ${!loading ? 'preloader-hidden' : ''}`}>
        <div className="preloader-content">
          <h1 className="preloader-title">Smart Form Filler</h1>
          <p className="preloader-caption">Intelligent Document Processing Made Easy</p>
        </div>
      </div>
    <div className={`upload-container ${!loading ? 'content-visible' : ''}`}>
      <h1 className="title">Upload Your ID Card</h1>

      <div className="upload-section">
        <div className="upload-options">
          <label className="file-upload-label">
            <Upload className="upload-icon" size={32} />
            <span>Click here or drop your ID card images</span>
            <input
              type="file"
              onChange={handleFileChange}
              multiple
              className="file-input"
              accept="image/*"
            />
          </label>

          <button
            className="camera-button"
            onClick={toggleCamera}
          >
            <Camera size={32} />
            <span>{showCamera ? 'Cancel Camera' : 'Use Camera'}</span>
            <div className="device-indicator">
              {isMobile ? <Smartphone size={16} /> : <Monitor size={16} />}
            </div>
          </button>
        </div>

        {showCamera && (
          <div className="camera-container">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className={currentFacingMode === 'user' ? 'camera-preview mirror' : 'camera-preview'}
            />
            {isCameraReady && (
              <div className="camera-controls">
                <button
                  className="capture-button"
                  onClick={capturePhoto}
                  title="Take Photo"
                >
                  <div className="capture-button-inner" />
                </button>
                
                <button
                  className="switch-camera-button"
                  onClick={switchCamera}
                  title="Switch Camera"
                >
                  <RotateCcw size={24} />
                </button>
              </div>
            )}
          </div>
        )}

        <div className={`preview-container ${files.length === 1 ? 'single-preview' : ''}`}>
          {filePreviews.map((preview, index) => (
            <div key={index} className="preview-card">
              <img
                src={preview}
                alt={`Uploaded ID ${index + 1}`}
                className="preview-image"
              />
              <div className="preview-overlay">
                <span className="preview-number">ID {index + 1}</span>
                <button
                  className="delete-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteFile(index);
                  }}
                  title="Delete Image"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {files.length > 0 && (
          <button
            onClick={handleUpload}
            className={`action-button upload-button ${isLoading ? 'loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="button-spinner"></div>
                Processing...
              </>
            ) : (
              <>
                <Upload size={20} />
                Process ID Cards
              </>
            )}
          </button>
        )}
      </div>

      {error && <p className="error-message">{error}</p>}

      {showScrollIndicator && !isLoading && Object.keys(extractedData).length === 0 && (
        <div className="scroll-indicator" onClick={scrollToExtractedData}>
          <span>View Extracted Data</span>
          <ChevronDown size={24} className="bounce" />
        </div>
      )}

      {Object.keys(extractedData).length > 0 && (
        <div className="extracted-data-section" ref={extractedDataRef}>
          <div className="section-header">
            <h2 className="section-title">Extracted Information</h2>
            <div className="edit-controls">
              {isEditing ? (
                <>
                  <button
                    onClick={handleUpdateData}
                    className="action-button save-button"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <div className="button-spinner"></div>
                    ) : (
                      <>
                        <Check size={20} />
                        Save Changes
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="action-button cancel-button"
                    disabled={isLoading}
                  >
                    <X size={20} />
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={handleEditToggle}
                  className="action-button edit-button"
                >
                  <Edit2 size={20} />
                  Edit Details
                </button>
              )}
            </div>
          </div>

          {renderExtractedData()}

            {!isEditing && (
              <button
                onClick={handleUploadForm}
                className="action-button next-button"
              >
                Continue to Form
                <ArrowRight size={20} />
              </button>
            )}
          </div>
        )}
      <div className="footer-container">
        <div className="logo-section">
          <h2 className="logo-text">Smart Form Filler</h2>
          <p className="logo-caption">Intelligent Document Processing Made Easy</p>
        </div>
      </div>
    </div>
    </>
  );
}

export default UploadID;