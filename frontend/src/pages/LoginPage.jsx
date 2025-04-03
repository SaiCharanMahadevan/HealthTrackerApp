import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom'; // Import Link
import { loginUser } from '../services/api'; // Import the API function

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null); // State for error messages
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null); // Clear previous errors
    try {
      console.log('Attempting login with:', email);
      const data = await loginUser(email, password);
      console.log('Login successful:', data);

      // Store the token (e.g., in localStorage)
      localStorage.setItem('authToken', data.access_token);

      // TODO: Update global auth state (will do this in App.jsx or context)

      // Navigate to the home page
      navigate('/');
      // Force a reload to update App state (temporary solution until proper state mgmt)
      window.location.reload();

    } catch (err) {
      console.error('Login failed:', err);
      setError(err.detail || 'Login failed. Please check your credentials.');
    }
  };

  return (
    <div className="form-container">
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
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
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Login</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <p>
        Don't have an account? <Link to="/signup">Sign Up</Link>
      </p>
    </div>
  );
}

export default LoginPage; 