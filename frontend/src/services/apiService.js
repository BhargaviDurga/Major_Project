import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:5000";

export const uploadID = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return axios.post(`${API_BASE_URL}/upload-id`, formData);
};
 
export const updateExtractedData = async (updatedData) => {
    return axios.post(`${API_BASE_URL}/update-data`, updatedData);
};

export const uploadForm = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return axios.post(`${API_BASE_URL}/fill-form`, formData, { responseType: 'blob' });
};
