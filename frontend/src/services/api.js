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

// Function to handle login
export const loginUser = async (email, password) => {
  try {
    // FastAPI's OAuth2PasswordRequestForm expects form data
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data; // Should contain { access_token: "...", token_type: "bearer" }
  } catch (error) {
    console.error('Login API error:', error.response || error.message);
    // Rethrow or handle specific error codes (e.g., 401 Unauthorized)
    throw error.response?.data || new Error('Login failed');
  }
};

// Function to handle signup
export const signupUser = async (email, password) => {
  try {
    const response = await apiClient.post('/auth/signup', {
      email,
      password,
    });
    return response.data; // Should contain user details (id, email, is_active)
  } catch (error) {
    console.error('Signup API error:', error.response || error.message);
    // Rethrow or handle specific error codes (e.g., 400 Bad Request - user exists)
    throw error.response?.data || new Error('Signup failed');
  }
};

// Function to get current user (requires auth token)
export const getCurrentUser = async (token) => {
    if (!token) throw new Error('No token provided');
    try {
        const response = await apiClient.get('/auth/me', {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        return response.data;
    } catch (error) {
        console.error('Get current user API error:', error.response || error.message);
        throw error.response?.data || new Error('Failed to fetch user');
    }
};

// Function to create a health entry
export const createHealthEntry = async (token, entryText) => {
  if (!token) throw new Error('No token provided');
  try {
    const response = await apiClient.post(
      '/entries/', 
      { entry_text: entryText }, // Send data as JSON body
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data; // The newly created entry
  } catch (error) {
    console.error('Create entry API error:', error.response || error.message);
    throw error.response?.data || new Error('Failed to create entry');
  }
};

// Function to get health entries
export const getHealthEntries = async (token, skip = 0, limit = 100) => {
  if (!token) throw new Error('No token provided');
  try {
    const response = await apiClient.get('/entries/', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: { skip, limit }, // Add query parameters for pagination
    });
    return response.data; // List of entries
  } catch (error) {
    console.error('Get entries API error:', error.response || error.message);
    throw error.response?.data || new Error('Failed to fetch entries');
  }
};

// We can add an interceptor later to automatically add the auth token to requests

export default apiClient; 