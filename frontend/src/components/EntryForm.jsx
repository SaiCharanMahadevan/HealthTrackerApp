import React, { useState } from 'react';
import apiService from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import dayjs from 'dayjs';

const EntryForm = ({ onEntryAdded }) => {
  const [text, setText] = useState('');
  const [entryDate, setEntryDate] = useState(dayjs().format('YYYY-MM-DD'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { token } = useAuth();

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!text.trim() || !token) {
      setError('Entry text cannot be empty.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = { 
        entry_text: text, 
        target_date_str: entryDate 
      };
      const newEntry = await apiService.addEntry(payload, token);
      onEntryAdded(newEntry);
      setText('');
    } catch (err) {
      console.error("Add entry failed:", err);
      setError(err.message || 'Failed to add entry.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="entry-form-card">
      <form onSubmit={handleSubmit}>
        <div className="form-group entry-form-date-picker">
          <label htmlFor="entry-date">Entry Date:</label>
          <input 
            type="date" 
            id="entry-date"
            value={entryDate}
            onChange={(e) => setEntryDate(e.target.value)}
            max={dayjs().format('YYYY-MM-DD')}
            required 
            disabled={loading}
            className="form-input"
          />
        </div>
        
        <div className="form-group">
          <textarea
            id="entry-text"
            rows="4"
            placeholder="Log your food, weight, or steps (e.g., '1 apple and 1 banana', 'Weight 80 kg', '10000 steps today')"
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
            required
          />
        </div>
        
        <button type="submit" className="form-button" disabled={loading}>
          {loading ? <LoadingSpinner size="small" /> : 'Log Entry'}
        </button>
        {error && <p className="error-message">{error}</p>}
      </form>
    </div>
  );
};

export default EntryForm; 