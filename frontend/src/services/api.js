import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
});

export const scanContract = async (sourceCode) => {
  try {
    const response = await api.post('/scan', { source_code: sourceCode });
    return response.data;
  } catch (error) {
    throw error.response?.data || error.message;
  }
};