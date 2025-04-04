import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import useAuth from '../hooks/useAuth';

// Helper function to display parsed data (adapt as needed based on actual backend response)
const displayParsedData = (entry) => {
    if (!entry || !entry.entry_type || entry.entry_type === 'unknown' || entry.entry_type === 'error') {
        return <span>{entry?.entry_text || 'Invalid entry data'}</span>; // Fallback to raw text or error message
    }

    try {
        switch (entry.entry_type) {
            case 'weight':
                return <span>Weight: {entry.value} {entry.unit || ''}</span>;
            case 'steps':
                return <span>Steps: {entry.value}</span>;
            case 'food':
                // Assuming parsed_data is a JSON string, parse it
                const foodData = typeof entry.parsed_data === 'string' ? JSON.parse(entry.parsed_data) : entry.parsed_data;
                
                if (foodData && foodData.items && Array.isArray(foodData.items)) {
                    const items = foodData.items.map((item, index) => (
                        <span key={index}>
                            {item.quantity} {item.unit || ''} {item.item}
                            ({item.calories ? `${item.calories} kcal` : 'N/A'})
                            {index < foodData.items.length - 1 ? ', ' : ''}
                        </span>
                    ));
                    const totals = foodData.total_calories !== undefined
                        ? ` | Total: ${foodData.total_calories} kcal, P:${foodData.total_protein_g || '?'}g, C:${foodData.total_carbs_g || '?'}g, F:${foodData.total_fat_g || '?'}g`
                        : '';
                    return <span>Food: {items}{totals}</span>;
                } else {
                    console.warn("Food entry missing expected parsed_data structure:", entry);
                    return <span>Food: {entry.entry_text} (parsing details unavailable)</span>;
                }
            default:
                return <span>{entry.entry_text}</span>;
        }
    } catch (e) {
        console.error("Error rendering parsed data:", e, entry);
        return <span>{entry.entry_text} (display error)</span>;
    }
};


const EntryList = ({ entries, setEntries }) => { // Receive entries and setter from parent
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { token } = useAuth();

    useEffect(() => {
        const fetchEntries = async () => {
            if (!token) return; // Don't fetch if not logged in
            setLoading(true);
            setError(null);
            try {
                const fetchedEntries = await apiService.getEntries(token);
                // Sort entries by timestamp, newest first
                fetchedEntries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                setEntries(fetchedEntries); 
            } catch (err) {
                setError(err.message || 'Failed to fetch entries.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchEntries();
    }, [token, setEntries]); // Re-fetch if token changes

    if (loading) {
        return <p>Loading entries...</p>;
    }

    if (error) {
        return <p className="error-message">Error loading entries: {error}</p>;
    }

    return (
        <div className="entry-list-card"> {/* Style container */} 
            {entries.length > 0 ? (
                <ul>
                    {entries.map((entry) => (
                        <li key={entry.id}>
                            <strong>{new Date(entry.timestamp).toLocaleString()}:</strong>
                            <div className="entry-content">{displayParsedData(entry)}</div>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No entries yet. Add one above!</p>
            )}
        </div>
    );
};

export default EntryList; 