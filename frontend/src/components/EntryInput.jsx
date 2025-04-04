import React, { useState } from 'react';
import apiService from '../services/api';
import useAuth from '../hooks/useAuth';

const EntryInput = ({ onEntryAdded }) => {
    const [entryText, setEntryText] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { token } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!entryText.trim() || !token) {
            setError('Entry text cannot be empty and you must be logged in.');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const newEntry = await apiService.createEntry(entryText, token);
            setEntryText(''); // Clear input
            if (onEntryAdded) {
                onEntryAdded(newEntry); // Notify parent component
            }
        } catch (err) {
            setError(err.message || 'Failed to save entry');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="entry-input-card"> {/* Style container */} 
            <form onSubmit={handleSubmit}>
                <textarea
                    rows="4"
                    value={entryText}
                    onChange={(e) => setEntryText(e.target.value)}
                    placeholder="Log your food, weight, or steps (e.g., '1 apple and 1 banana', 'Weight 80 kg', '10000 steps today')"
                    required
                    disabled={loading}
                />
                {error && <p className="error-message">{error}</p>}
                <button type="submit" disabled={loading}>
                    {loading ? 'Logging...' : 'Log Entry'}
                </button>
            </form>
        </div>
    );
};

export default EntryInput; 