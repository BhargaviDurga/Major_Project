import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Download, RefreshCw, AlertTriangle, Check, Share2, Copy, Send, Star } from 'lucide-react';
import { Alert, AlertDescription } from './Alert';
import './SuccessPage.css';

export default function SuccessPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const [downloadError, setDownloadError] = useState(false);
    const [showCopySuccess, setShowCopySuccess] = useState(false);
    const [rating, setRating] = useState(0);
    const [query, setQuery] = useState('');
    const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
    const [countdown, setCountdown] = useState(() => {
        // Check if there's an existing expiration time in sessionStorage
        const expirationTime = sessionStorage.getItem('formExpirationTime');
        if (expirationTime) {
            const remainingTime = Math.max(0, Math.floor((parseInt(expirationTime) - Date.now()) / 1000));
            return remainingTime > 0 ? remainingTime : 0;
        }
        // If no existing expiration time, set it to 5 minutes (300 seconds) from now
        const newExpirationTime = Date.now() + (60 * 1000); // 5 minutes in milliseconds
        sessionStorage.setItem('formExpirationTime', newExpirationTime.toString());
        return 60;
    });

    const { pdfBlob, fileName = 'filled_form.pdf' } = location.state || {};

    useEffect(() => {
        // If session is already expired, redirect immediately
        if (countdown === 0) {
            navigate('/upload-id');
            return;
        }

        const timer = setInterval(() => {
            const expirationTime = parseInt(sessionStorage.getItem('formExpirationTime'));
            const now = Date.now();
            const remaining = Math.max(0, Math.floor((expirationTime - now) / 1000));

            if (remaining <= 0) {
                clearInterval(timer);
                sessionStorage.removeItem('formExpirationTime');
                navigate('/upload-id');
                setCountdown(0);
            } else {
                setCountdown(remaining);
            }
        }, 1000);


        return () => clearInterval(timer);
    }, [countdown, navigate]);

    const handleDownload = () => {
        if (pdfBlob) {
            try {
                const blobUrl = window.URL.createObjectURL(pdfBlob);
                const link = document.createElement('a');
                link.href = blobUrl;
                link.download = fileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                setTimeout(() => {
                    window.URL.revokeObjectURL(blobUrl);
                }, 100);
                setDownloadError(false);
            } catch (error) {
                console.error('Download error:', error);
                setDownloadError(true);
            }
        } else {
            setDownloadError(true);
        }
    };

    const handleStartOver = () => {
        sessionStorage.removeItem('formExpirationTime');
        navigate('/upload-id');
    };

    const handleShare = async () => {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Filled Form',
                    text: 'Check out my filled form from Smart Form Filler',
                    url: window.location.href
                });
            } catch (error) {
                console.error('Share failed:', error);
            }
        }
    };

    const handleCopyLink = () => {
        navigator.clipboard.writeText(window.location.href);
        setShowCopySuccess(true);
        setTimeout(() => setShowCopySuccess(false), 2000);
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const emojis = ['😞', '🙁', '😐', '🙂', '😊'];

    const handleRating = (value) => {
        setRating(value);
    };

    const handleSubmitFeedback = () => {
        // Here you would typically send the feedback to your backend
        console.log('Feedback submitted:', { rating, query });
        setFeedbackSubmitted(true);
        // Reset form
        setQuery('');
    };

    return (
        <div className="success-container">
            <div className="success-content">
                <div className="checkmark-container">
                    <svg className="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                        <circle className="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                        <path className="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                    </svg>
                </div>
                
                <h1 className="success-title">
                    Thanks for using
                    <span className="highlight"> Smart Form Filler</span>
                </h1>

                {countdown > 0 && (
                    <div className={`session-timer ${countdown <= 30 ? 'warning' : ''}`}>
                        Session expires in: {formatTime(countdown)}
                    </div>
                )}

                <div className="success-actions">
                    <button 
                        className="action-button download-button"
                        onClick={handleDownload}
                        disabled={!pdfBlob || countdown === 0}
                    >
                        <Download size={20} />
                        Download Filled Form
                    </button>

                    {downloadError && (
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                                The filled form is no longer available. Please start over with a new form.
                            </AlertDescription>
                        </Alert>
                    )}

                    <div className="share-actions">
                        {navigator.share && (
                            <button 
                                className="action-button share-button"
                                onClick={handleShare}
                            >
                                <Share2 size={20} />
                                Share
                            </button>
                        )}
                        <button 
                            className="action-button copy-button"
                            onClick={handleCopyLink}
                        >
                            {showCopySuccess ? <Check size={20} /> : <Copy size={20} />}
                            {showCopySuccess ? 'Copied!' : 'Copy Link'}
                        </button>
                    </div>

                    <button 
                        className="action-button restart-button"
                        onClick={handleStartOver}
                    >
                        <RefreshCw size={20} />
                        Fill Another Form
                    </button>
                </div>

                <div className="security-notice">
                    <AlertTriangle size={16} />
                    <p>Your credentials will be removed and you'll be redirected in {formatTime(countdown)}.</p>
                </div>
                {!feedbackSubmitted ? (
                    <div className="feedback-section">
                        <h2 className="feedback-title">How was your experience?</h2>
                        
                        <div className="rating-container">
                            {emojis.map((emoji, index) => (
                                <button
                                    key={index}
                                    className={`emoji-button ${rating === index + 1 ? 'selected' : ''}`}
                                    onClick={() => handleRating(index + 1)}
                                >
                                    <span className="emoji">{emoji}</span>
                                    <span className="rating-value">{index + 1}</span>
                                </button>
                            ))}
                        </div>

                        <div className="query-section">
                            <textarea
                                className="query-input"
                                placeholder="Any questions or feedback? We'd love to hear from you!"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                rows={3}
                            />
                            <button
                                className="submit-feedback-button"
                                onClick={handleSubmitFeedback}
                                disabled={!rating}
                            >
                                <Send size={16} />
                                Submit Feedback
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="feedback-success">
                        <div className="feedback-success-content">
                            <Check size={32} className="feedback-check" />
                            <h2>Thank you for your feedback!</h2>
                            <p>We appreciate your time and input.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}