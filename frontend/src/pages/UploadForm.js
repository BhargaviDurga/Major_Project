import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import FileUpload from "../components/FileUpload";
import LoadingSpinner from "../components/LoadingSpinner";
import PDFPreview from "../components/PDFPreview";
import { Upload, ArrowLeft, FileText, ExternalLink, Download,Check } from 'lucide-react';
import './UploadForm.css';

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
        if (!pdfFile) {
            setError("Please select a PDF file first");
            return;
        }
        setError(null);
        setLoading(true);
        const formData = new FormData();
        formData.append('file', pdfFile);

        try {
            const response = await axios.post('http://localhost:5000/fill-form', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                responseType: 'blob',
            });
            const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
            setFilledPdfUrl(url);
        } catch (error) {
            console.error("Error uploading PDF:", error);
            setError("Failed to process the PDF. Please try again.");
        } finally {
            setLoading(false);
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