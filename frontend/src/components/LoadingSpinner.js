import './styledcomponents.css';
import React, { useState, useEffect } from 'react';

const LoadingSpinner = ({ messages }) => {
    const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  
    useEffect(() => {
      if (messages.length > 1) {
        const timer = setTimeout(() => {
          setCurrentMessageIndex((prevIndex) => (prevIndex + 1) % messages.length);
        }, 5000); // Change message every 5 seconds
  
        return () => clearTimeout(timer);
      }
    }, [currentMessageIndex, messages]);
    
    return (
        <div className="loading-spinner">
            <div className="spinner"></div>
            <p className="loading-message">{messages[currentMessageIndex]}</p>
        </div>
    );
}

export default LoadingSpinner;

