import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, Navigate, useNavigate, useLocation } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import './App.css';

// Simple Protected Route Component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('authToken');
  if (!token) {
    // Redirect them to the /login page, but save the current location they were
    // trying to go to when they were redirected. This allows us to send them
    // along to that page after they login, which is a nicer user experience
    // than dropping them off on the home page.
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const navigate = useNavigate(); // Need navigate for logout
  const location = useLocation(); // Get current location

  // Define routes where the main navigation should be hidden
  const hideNavRoutes = ['/login', '/signup'];
  const shouldHideNav = hideNavRoutes.includes(location.pathname);

  // Effect to update state if token changes in localStorage (e.g., after login)
  // This is a basic approach; context/state management libraries are better for complex apps
  useEffect(() => {
    const handleStorageChange = () => {
      setToken(localStorage.getItem('authToken'));
    };
    // Listen for custom event dispatched after login/logout if needed, or poll
    // For simplicity, we rely on the page reload in LoginPage for now
    // A better way is needed if we remove the reload
    setToken(localStorage.getItem('authToken')); // Initial check

    // A more robust way: listen to storage events (only works across tabs/windows)
    // window.addEventListener('storage', handleStorageChange);
    // return () => window.removeEventListener('storage', handleStorageChange);

  }, []);

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    navigate('/login'); // Redirect to login after logout
     // Optionally force reload if needed: window.location.reload();
  };

  return (
    <div className="App">
      {/* Conditionally render the nav */} 
      {!shouldHideNav && (
        <nav>
          <ul>
            <li><Link to="/">Home</Link></li>
            {!token ? (
              <>
                <li><Link to="/login">Login</Link></li>
                <li><Link to="/signup">Sign Up</Link></li>
              </>
            ) : (
              <li><button onClick={handleLogout}>Logout</button></li>
            )}
          </ul>
        </nav>
      )}

      <main>
        <Routes>
           {/* Protected Home Route */}
          <Route 
            path="/"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          {/* Redirect root to login if not authenticated? Or keep separate? */}
          {/* Consider adding a 404 Not Found route */}
        </Routes>
      </main>
    </div>
  );
}

// App needs to be wrapped by BrowserRouter, so useNavigate works
// We ensure this in main.jsx

export default App;
