import React, { createContext, useState, useEffect } from 'react';
import apiService from '../services/api'; // Ensure apiService is imported

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(localStorage.getItem('authToken'));
    const [user, setUser] = useState(null); // Store user info if needed
    const [loading, setLoading] = useState(true); // Handle initial loading state

    // Fetch user details if token exists on load or when token changes
    useEffect(() => {
        const fetchUser = async () => {
            // Reset user state when token is removed
            if (!token) {
                setUser(null);
                setLoading(false);
                return; 
            }

            setLoading(true); // Set loading true when starting fetch
            try {
                console.log("Token found, attempting to fetch user...");
                const userData = await apiService.getCurrentUser(token);
                console.log("Fetched user data:", userData);
                setUser(userData); // Set the fetched user data
            } catch (error) {
                console.error("Failed to fetch user with token:", error);
                // If fetching user fails (e.g., invalid token), log out
                localStorage.removeItem('authToken');
                setToken(null); 
                setUser(null);
            } finally {
                setLoading(false); // Ensure loading is set to false after attempt
            }
        };

        fetchUser();
    }, [token]); // Re-run effect if token changes

    const login = (newToken) => {
        // Set the token first, the useEffect above will trigger user fetch
        localStorage.setItem('authToken', newToken);
        setToken(newToken); 
        // setUser state will be updated by the useEffect hook
    };

    const logout = () => {
        localStorage.removeItem('authToken');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ token, user, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext; 