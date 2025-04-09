import React, { createContext, useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api'; // Ensure apiService is imported

const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => {
    return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(() => localStorage.getItem('authToken'));
    const [user, setUser] = useState(null); // Store user info if needed
    const [loading, setLoading] = useState(true); // Handle initial loading state
    const navigate = useNavigate(); // Hook for navigation

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
                console.log("AuthContext: Token found, attempting to fetch user...");
                const userData = await apiService.getCurrentUser(token);
                console.log("AuthContext: Fetched user data:", userData);
                setUser(userData); // Set the fetched user data
            } catch (error) {
                console.error("AuthContext: Failed to fetch user with token:", error);
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

    // Updated login function
    const login = async (email, password) => {
        console.log("AuthContext: login function called with", email);
        try {
            // Call the API service to get the token
            const data = await apiService.login(email, password); 
            const newToken = data.access_token;
            console.log("AuthContext: API login successful, got token:", newToken);
            
            // Set token in localStorage and state
            localStorage.setItem('authToken', newToken);
            setToken(newToken); 
            // The useEffect will now fetch the user based on the new token
            
            // Navigate to DIARY page AFTER successful login and token set, replacing history
            console.log("AuthContext: Navigating to /diary after login");
            navigate('/diary', { replace: true });
            
        } catch (error) {
            console.error("AuthContext: API login failed:", error);
            // Re-throw the error so LoginPage can display it
            throw error; 
        }
    };

    // Updated logout function
    const logout = () => {
        console.log("AuthContext: logout function called");
        localStorage.removeItem('authToken');
        setToken(null);
        setUser(null);
        // Navigate to login page after logout
        console.log("AuthContext: Navigating to /login after logout");
        navigate('/login'); 
    };

    return (
        <AuthContext.Provider value={{ 
            token,
            user,
            isAuthenticated: !!token, // Derived state: user is authenticated if token exists
            login,
            logout,
            loading 
        }}>
            {children}
        </AuthContext.Provider>
    );
}; 