import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {useAuth} from '../contexts/AuthContext';
import apiService from '../services/api';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null); // State for error messages
  const navigate = useNavigate(); // Still needed for potential redirects *from* login page (e.g., signup link)
  const { login: contextLogin } = useAuth(); // Get the login function from context
  const [isSubmitting, setIsSubmitting] = useState(false); // Keep submitting state

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isSubmitting) return; // Prevent double submit

    setError(null);
    setIsSubmitting(true);

    try {
      console.log('LoginPage: Calling context login with:', email);
      await contextLogin(email, password);
      console.log('LoginPage: Context login successful (navigation handled by context)');
    } catch (err) {
      console.error('LoginPage: Context login failed:', err);
      setError(err.message || 'Login failed. Please check your credentials.');
      setIsSubmitting(false); // Re-enable button on error
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
        <button type="submit" className="form-button" disabled={isSubmitting}>
           {isSubmitting ? 'Logging in...' : 'Login'}
         </button>
      </form>
      {error && <p className="error-message">{error}</p>}
      <p>
        Don't have an account? <Link to="/signup">Sign Up</Link>
      </p>
    </div>
  );
}

export default LoginPage; 