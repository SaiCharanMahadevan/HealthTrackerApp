import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {useAuth} from '../contexts/AuthContext';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null); // State for error messages
  const navigate = useNavigate(); // Still needed for potential redirects *from* login page (e.g., signup link)
  const { login } = useAuth(); // Get the login function from context

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null); // Clear previous errors
    try {
      console.log('LoginPage: Calling context login with:', email);
      // Call the login function from AuthContext
      await login(email, password); 
      // Navigation will now be handled within the AuthContext's login function
      // No need for navigate('/') or reload here
      console.log('LoginPage: Context login successful');
    } catch (err) {
      console.error('LoginPage: Context login failed:', err);
      // Use err.message from the context/apiService call
      setError(err.message || 'Login failed. Please check your credentials.');
    }
  };

  return (
    <div className="form-container login-page-container">
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
            className="form-input"
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input
            className="form-input"
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="form-button">Login</button>
      </form>
      {error && <p className="error-message">{error}</p>}
      <p>
        Don't have an account? <Link to="/signup">Sign Up</Link>
      </p>
    </div>
  );
}

export default LoginPage; 