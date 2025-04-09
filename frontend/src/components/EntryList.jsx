import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback } from 'react';
import apiService from '../services/api';
import {useAuth} from '../contexts/AuthContext';
import { formatValue, formatLocalDateTime } from '../utils/formatters'; // Keep this formatter import
import LoadingSpinner from './LoadingSpinner';

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

const EntryList = forwardRef(({ entries, setEntries, onEntryUpdated, onEntryDeleted, onEditClick }, ref) => {
    const [listLoading, setListLoading] = useState(false); 
    const [listError, setListError] = useState(null); 
    const { token } = useAuth();

    // Expose refetch method
    const fetchEntries = useCallback(async () => {
            if (!token) return;
            setListLoading(true);
            setListError(null);
            try {
                const fetchedEntries = await apiService.getEntries(token);
                fetchedEntries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                setEntries(fetchedEntries);
            } catch (err) {
                setListError(err.message || 'Failed to fetch entries.');
                console.error(err);
            } finally {
                setListLoading(false);
            }
    }, [token, setEntries]);

    useEffect(() => {
        fetchEntries();
    }, [fetchEntries]);
    
    useImperativeHandle(ref, () => ({
        refetch: fetchEntries
    }));

    const handleDelete = async (entryId) => {
        if (!window.confirm("Are you sure you want to delete this entry?")) {
            return;
        }
        try {
            await apiService.deleteEntry(entryId, token);
            onEntryDeleted(entryId); // Notify parent to update state
        } catch (err) {
            console.error("Delete failed:", err);
            setListError(err.message || 'Failed to delete entry.'); // Show error related to the list
        }
    };

    if (listLoading) return <LoadingSpinner />;
    if (listError) return <p className="error-message">Error: {listError}</p>;

    return (
        <div className="entry-list-card"> 
            {entries.length > 0 ? (
                <ul> 
                    {entries.map((entry) => (
                        <li key={entry.id}>
                            <strong>{formatLocalDateTime(entry.timestamp)}:</strong> 
                            <div className="entry-content">
                                {displayParsedData(entry)}
                                </div>
                                    <div className="entry-actions">
                                <button 
                                    onClick={() => onEditClick(entry)} 
                                    className="button-edit"
                                    aria-label={`Edit entry from ${formatLocalDateTime(entry.timestamp)}`}
                                >
                                            Edit
                                        </button>
                                <button 
                                    onClick={() => handleDelete(entry.id)} 
                                    className="button-delete"
                                    aria-label={`Delete entry from ${formatLocalDateTime(entry.timestamp)}`}
                                >
                                            Delete
                                        </button>
                                    </div>
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No entries logged yet.</p>
            )}
        </div>
    );
});

export default EntryList; 