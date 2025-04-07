import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {useAuth} from '../contexts/AuthContext';

function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login'); // Redirect to login after logout
  };

  return isAuthenticated && (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">HealthTracker</Link> 
        </div>
      
      <ul className="navbar-links">
        <li>
          {/* Link to Diary Page */}
          <Link to="/">Diary</Link>
        </li>
        <li>
          {/* Link to Reports Page */}
          <Link to="/reports">Reports</Link>
        </li>
        <li>
          <button onClick={handleLogout} className="logout-button">Logout</button>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar; 