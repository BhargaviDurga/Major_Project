import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import FileUpload from "../components/FileUpload";
import LoadingSpinner from "../components/LoadingSpinner";
import PDFPreview from "../components/PDFPreview";
import { Upload, ArrowLeft, FileText, ExternalLink, Download,Check } from 'lucide-react';
import './UploadForm.css';

const apiUrl = process.env.REACT_APP_API_URL;

export default function UploadForm() {
    const navigate = useNavigate();
    const location = useLocation();
    const [pdfFile, setPdfFile] = useState(null);
    const [pdfPreviewUrl, setPdfPreviewUrl] = useState(null);
    const [filledPdfUrl, setFilledPdfUrl] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { idFiles, extractedData } = location.state || {};

    const handlePdfSelect = (file) => {
        setPdfFile(file);
        // Create URL for preview when file is selected
        if (file) {
            const previewUrl = URL.createObjectURL(file);
            setPdfPreviewUrl(previewUrl);
        } else {
            setPdfPreviewUrl(null);
        }
    };

const handlePdfUpload = async () => {
    if (!pdfFile || !extractedData) {
        setError(!pdfFile ? "Please select a PDF file first" : "No extracted data available");
        return;
    }
    setError(null);
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', pdfFile);
    formData.append('extracted_data', JSON.stringify(extractedData));

    try {
        console.log("Uploading file and data:", {
            pdfFile: pdfFile.name,
            extractedData: Object.keys(extractedData)
        });
        
        const response = await axios.post(`${apiUrl}/fill-form`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            responseType: 'blob',
            timeout: 200000,
            onUploadProgress: progressEvent => {
                const percentCompleted = Math.round(
                    (progressEvent.loaded * 100) / progressEvent.total
                );
                console.log(`Upload progress: ${percentCompleted}%`);
            }
        });

        // Verify response is PDF
        if (!response.headers['content-type']?.includes('application/pdf')) {
            const errorData = await response.data.text();
            throw new Error(errorData || "Server returned invalid PDF response");
        }

        const url = URL.createObjectURL(response.data);
        setFilledPdfUrl(url);
        
        // Store the filled PDF in session storage
        const reader = new FileReader();
        reader.readAsDataURL(response.data);
        reader.onloadend = () => {
            sessionStorage.setItem('filledPdf', reader.result);
        };
        
    } catch (error) {
        let errorMessage = "Failed to process form";
        
        if (error.response) {
            // Handle different error response types
            if (error.response.data instanceof Blob) {
                try {
                    const errorText = await error.response.data.text();
                    const errorJson = safeJsonParse(errorText);
                    errorMessage = errorJson?.message || errorText || `Server error (${error.response.status})`;
                } catch {
                    errorMessage = `Server error (${error.response.status})`;
                }
            } else if (typeof error.response.data === 'object') {
                errorMessage = error.response.data.message || 
                              `Server error (${error.response.status})`;
            }
        } else if (error.code === 'ECONNABORTED') {
            errorMessage = "Request timed out. Please try again.";
        } else if (error.request) {
            errorMessage = "No response from server. Please check your connection.";
        } else {
            errorMessage = error.message || "An unknown error occurred";
        }
        
        console.error("PDF processing error:", {
            error: error,
            endpoint: `${apiUrl}/fill-form`,
            requestData: {
                pdfFile: pdfFile.name,
                dataFields: Object.keys(extractedData)
            }
        });
        
        setError(errorMessage);
    } finally {
        setLoading(false);
    }
};

// Helper function to safely parse JSON
const safeJsonParse = (str) => {
    try {
        return JSON.parse(str);
    } catch {
        return null;
    }
};

    const handleDownloadAndRedirect = () => {
        if (filledPdfUrl) {
            // Create a link element and trigger download
            const link = document.createElement('a');
            link.href = filledPdfUrl;
            link.download = 'filled_form.pdf';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            fetch(filledPdfUrl)
            .then(response => response.blob())
            .then(blob => {
                // Pass both the blob and its URL to the success page
                navigate('/success', { 
                    state: { 
                        pdfBlob: blob,
                        fileName: 'filled_form.pdf'
                    } 
                });
            });
        }
    };

    const handleOpenPdf = () => {
        if (pdfPreviewUrl) {
            window.open(pdfPreviewUrl, '_blank');
        }
    };

    const handleBack = () => {
        navigate('/upload-id', { state: { idFiles, extractedData } });
    };

    // Cleanup URLs when component unmounts
    React.useEffect(() => {
        return () => {
            if (pdfPreviewUrl) URL.revokeObjectURL(pdfPreviewUrl);
            if (filledPdfUrl) URL.revokeObjectURL(filledPdfUrl);
        };
    }, [pdfPreviewUrl, filledPdfUrl]);

    return (
        <div className="form-upload-container">
            <div className="form-header">
                <button onClick={handleBack} className="back-button">
                    <ArrowLeft size={20} />
                        Back to ID Upload
                </button>
                <h2 className="form-title">Upload Your Form</h2>
            </div>

            <div className="upload-section">
                <div className="upload-card">
                    <FileUpload 
                        label={
                            <div className="upload-label-content">
                                <FileText size={32} />
                                <span>Select or drop your PDF form here</span>
                            </div>
                        } 
                        onFileSelect={handlePdfSelect} 
                    />
                    
                    {pdfFile && (
                        <div className="selected-file" onClick={handleOpenPdf}>
                            <FileText size={20} />
                            <span>{pdfFile.name}</span>
                            <ExternalLink size={16} className="preview-icon" />
                            <span className="preview-text">Click to preview</span>
                        </div>
                    )}

                    {error && <div className="error-message">{error}</div>}

                    <button 
                        onClick={handlePdfUpload} 
                        className={`action-button upload-button ${loading ? 'loading' : ''}`}
                        disabled={loading || !pdfFile}
                    >
                        {loading ? (
                            <>
                                <div className="button-spinner"></div>
                                Processing...
                            </>
                        ) : (
                            <>
                                <Upload size={20} />
                                Process Form
                            </>
                        )}
                    </button>
                </div>
            </div>

            {loading && (
                <div className="loading-container">
                    <LoadingSpinner messages={["Filling your form...", "This may take a while....Please wait....."]} />
                </div>
            )}

            {filledPdfUrl && (
                <div className="preview-section">
                    <h3 className="preview-title">Filled Form Preview</h3>
                    <PDFPreview pdfUrl={filledPdfUrl} />
                    <button 
                        onClick={handleDownloadAndRedirect}
                        className="action-button download-button"
                    >
                        <Download size={20} />
                        Download Form
                    </button>
                </div>
            )}
            <div className="footer-container">
                <div className="logo-section">
                    <h2 className="logo-text">Smart Form Filler</h2>
                    <p className="logo-caption">Intelligent Document Processing Made Easy</p>
                </div>
            </div>
        </div>
    );
}