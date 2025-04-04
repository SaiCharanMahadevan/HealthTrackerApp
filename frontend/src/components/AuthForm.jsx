import React, { useState } from 'react';
import useAuth from '../hooks/useAuth';
import apiService from '../services/api';

const AuthForm = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLogin, setIsLogin] = useState(true);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const { login } = useAuth(); // Get the login function from context

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            if (isLogin) {
                const data = await apiService.login(email, password);
                login(data.access_token); // Update auth context
                // Redirect happens in App.jsx based on token presence
            } else {
                await apiService.signup(email, password);
                // Optionally login immediately after signup
                const data = await apiService.login(email, password);
                login(data.access_token);
                // Or show a success message and prompt user to login
                // alert('Signup successful! Please login.');
                // setIsLogin(true);
            }
        } catch (err) {
            setError(err.message || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-form-card">
            <h1>Welcome</h1>
            <p>Please login or sign up</p>
            
            <h2>{isLogin ? 'Login' : 'Sign Up'}</h2>
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
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <button type="submit" disabled={loading}>
                    {loading ? 'Processing...' : (isLogin ? 'Login' : 'Sign Up')}
                </button>
            </form>
            <button onClick={() => setIsLogin(!isLogin)} disabled={loading}>
                Switch to {isLogin ? 'Sign Up' : 'Login'}
            </button>
        </div>
    );
};

export default AuthForm; 