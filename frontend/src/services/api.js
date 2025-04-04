import axios from 'axios';

// Define the base URL for the backend API
// In development, this might be http://localhost:8000/api/v1
// It's good practice to use environment variables for this
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const handleResponse = async (response) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('API Error:', errorData);
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    // Handle cases where response might be empty (e.g., 204 No Content)
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
        return response.json();
    } else {
        return {}; // Return empty object or handle as needed
    }
};

const apiService = {
    signup: async (email, password) => {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });
        return handleResponse(response);
    },

    login: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        });
        return handleResponse(response); // Returns { access_token, token_type }
    },

    getCurrentUser: async (token) => {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        return handleResponse(response);
    },

    createEntry: async (entryText, token) => {
        const response = await fetch(`${API_BASE_URL}/entries/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ entry_text: entryText }),
        });
        return handleResponse(response);
    },

    getEntries: async (token, skip = 0, limit = 100) => {
        const response = await fetch(`${API_BASE_URL}/entries/?skip=${skip}&limit=${limit}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        return handleResponse(response);
    },

    getWeeklySummary: async (token, targetDate = null) => {
        let url = `${API_BASE_URL}/reports/summary/weekly`;
        if (targetDate) {
            // Assuming targetDate is in YYYY-MM-DD format
            url += `?target_date_str=${targetDate}`;
        }
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        return handleResponse(response);
    },

    getTrends: async (token, startDate = null, endDate = null) => {
        let url = `${API_BASE_URL}/reports/trends`;
        const params = new URLSearchParams();
        if (startDate) {
            params.append('start_date_str', startDate); // YYYY-MM-DD
        }
        if (endDate) {
            params.append('end_date_str', endDate); // YYYY-MM-DD
        }
        const queryString = params.toString();
        if (queryString) {
            url += `?${queryString}`;
        }

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        return handleResponse(response);
    },
};

export default apiService; 