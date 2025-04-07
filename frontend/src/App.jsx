import React from 'react';
import {
    Routes,
    Route,
    Navigate
} from 'react-router-dom';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DiaryPage from './pages/DiaryPage'; 
import ReportsPage from './pages/ReportsPage';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoadingSpinner from './components/LoadingSpinner';
import './App.css';

// PrivateRoute component to protect routes
function PrivateRoute({ children }) {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}><LoadingSpinner /></div>;
    }

    return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function App() {
    return (
        <AuthProvider>
            <Navbar />
            <div className="main-content">
                <Routes>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/signup" element={<SignupPage />} />
                    
                    {/* Protected Routes */}
                    <Route 
                        path="/" 
                        element={
                            <PrivateRoute>
                                <DiaryPage />
                            </PrivateRoute>
                        }
                    />
                    <Route 
                        path="/reports" 
                        element={
                            <PrivateRoute>
                                <ReportsPage />
                            </PrivateRoute>
                        }
                    />
                    
                    {/* Fallback or redirect for any other path */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </div>
        </AuthProvider>
    );
}

export default App;
