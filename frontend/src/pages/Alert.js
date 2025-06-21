import React from 'react';
import './Alert.css';

export const Alert = ({ variant, children }) => {
  return (
    <div className={`alert alert-${variant}`}>
      {children}
    </div>
  );
};

export const AlertDescription = ({ children }) => {
  return (
    <div className="alert-description">
      {children}
    </div>
  );
};