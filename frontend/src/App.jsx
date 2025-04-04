import React from 'react';
import {
    BrowserRouter as Router, // Corrected: Was double-imported in main.jsx initially
    Routes,
    Route,
    Navigate
} from 'react-router-dom';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import useAuth from './hooks/useAuth';
import './App.css'; // Ensure App.css is imported
// import './App.css'; // Assuming you have App.css for styling

function App() {
    const { token, loading } = useAuth();

    if (loading) {
        // Optional: Show a loading spinner or message while checking auth state
        return <div>Loading...</div>;
    }

    return (
        // Router might be here or in main.jsx, ensure it's only in one place
        // If Router is in main.jsx, remove it from here.
        // <Router> 
            <div className="App">
                <Routes>
                    <Route 
                        path="/" 
                        element={token ? <HomePage /> : <Navigate to="/auth" replace />}
                    />
                    <Route 
                        path="/auth" 
                        element={!token ? <AuthPage /> : <Navigate to="/" replace />}
                    />
                    {/* Add other routes here */}
                    <Route path="*" element={<Navigate to="/" replace />} /> {/* Catch-all redirects to home */}
                </Routes>
            </div>
        // </Router>
    );
}

export default App;
