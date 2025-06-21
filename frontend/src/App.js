import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import UploadID from "./pages/UploadID";
import UploadForm from "./pages/UploadForm";
import SuccessPage from "./pages/SuccessPage";

export default function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<UploadID />} />
                <Route path="/upload-id" element={<UploadID />} />
                <Route path="/upload-form" element={<UploadForm />} />
                <Route path="/success" element={<SuccessPage />} />
            </Routes>
        </Router>
    );
}
