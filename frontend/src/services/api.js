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
    // Check for 204 No Content before trying to parse JSON
    if (response.status === 204) {
        return {}; // Or return null, depends on how you want to handle it downstream
    }

    // For other non-OK responses, try to parse error details
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! Status: ${response.status}` }));
        console.error('API Error:', errorData);
        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
    }

    // For successful responses with content, parse JSON
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
        return response.json();
    } else {
        // Handle successful responses that aren't JSON (if any are expected)
        return {}; 
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

    getDailySummary: async (token, targetDate = null) => {
        const params = new URLSearchParams();
        if (targetDate) {
            params.append('target_date_str', targetDate); // Already YYYY-MM-DD
        }
        
        // Get client's timezone offset in minutes (negative for east of UTC, positive for west)
        // getTimezoneOffset() returns minutes difference between UTC and local time.
        // e.g., SGT (UTC+8) is -480. We send this value directly.
        const tzOffsetMinutes = new Date().getTimezoneOffset();
        params.append('tz_offset_minutes', tzOffsetMinutes.toString());

        const url = `${API_BASE_URL}/reports/summary/daily?${params.toString()}`;
        console.log(`Fetching daily summary from: ${url}`); // Log the URL with params

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            console.error('Failed to fetch daily summary:', errorData);
            throw new Error(errorData.detail || 'Failed to fetch daily summary');
        }
        return response.json();
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

    updateEntry: async (entryId, entryData, token) => {
        const response = await fetch(`${API_BASE_URL}/entries/${entryId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(entryData), // Expects e.g., { entry_text: "new text" }
        });
        return handleResponse(response);
    },

    deleteEntry: async (entryId, token) => {
        const response = await fetch(`${API_BASE_URL}/entries/${entryId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        // DELETE often returns 204 No Content, handleResponse handles this
        // It might throw an error for non-2xx responses which we catch in the component
        return handleResponse(response); 
    },

    addEntry: async (entryData, token) => {

        const response = await fetch(`${API_BASE_URL}/entries/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(entryData),
        });
        return handleResponse(response); // Assume handleResponse exists and throws error on failure
    },
};

export default apiService; 