import axios from 'axios';

const api = axios.create({
    // Asegúrate de que este puerto coincida con tu backend (FastAPI suele ser 8000)
    baseURL: 'http://localhost:8000/api/v1', 
    headers: {
        'Content-Type': 'application/json',
    },
});

export default api;