import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback, useRef } from 'react';
import apiService from '../services/api';
import {useAuth} from '../contexts/AuthContext';
import { formatValue } from '../utils/formatters'; // formatLocalDate might not be needed here anymore
import dayjs from 'dayjs'; // Import dayjs
import LoadingSpinner from './LoadingSpinner'; // Import the spinner

const DailySummaryDisplay = forwardRef((props, ref) => {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    // State for the selected date, default to today in YYYY-MM-DD format
    const [selectedDate, setSelectedDate] = useState(dayjs().format('YYYY-MM-DD')); 
    const { token } = useAuth();
    const dateInputRef = useRef(null); // Ref for the date input

    // Fetch summary data for a specific date
    const fetchSummary = useCallback(async (dateStr) => {
        if (!token || !dateStr) {
            // setError("Missing token or date."); // Optional: more specific error
            return; 
        }
        setLoading(true);
        setError(null);
        try {
            // Pass the selected date string (YYYY-MM-DD) to the API
            const data = await apiService.getDailySummary(token, dateStr); 
            setSummary(data);
        } catch (err) {
            setError(err.message || 'Failed to fetch daily summary.');
            setSummary(null); // Clear summary on error
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [token]); // Dependency: token. fetchSummary itself doesn't depend on selectedDate

    // Fetch data when component mounts or selectedDate changes
    useEffect(() => {
        fetchSummary(selectedDate);
    }, [selectedDate, fetchSummary]); // Re-run when selectedDate or fetchSummary changes

    // Expose a refetch method to the parent component
    useImperativeHandle(ref, () => ({ 
        // Refetch should use the currently selected date
        refetch: () => fetchSummary(selectedDate) 
    }));

    // --- New Date Navigation Functions ---
    const goToPreviousDay = () => {
        setSelectedDate(dayjs(selectedDate).subtract(1, 'day').format('YYYY-MM-DD'));
    };

    const goToNextDay = () => {
        setSelectedDate(dayjs(selectedDate).add(1, 'day').format('YYYY-MM-DD'));
    };

    const openDatePicker = () => {
        dateInputRef.current?.click(); // Programmatically click the hidden input
    };
    // --- End New Functions ---

    // Handle date input change
    const handleDateChange = (event) => {
        setSelectedDate(event.target.value); // Value is already YYYY-MM-DD
    };

    // Render logic
    const renderContent = () => {
        // Show spinner centrally while loading
        if (loading) {
            // Wrap spinner in a centering div
            return (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100px' /* Add min-height */ }}>
                    <LoadingSpinner />
                </div>
            );
        }
        if (error) {
            return <p className="error-message">Error: {error}</p>;
        }
        if (!summary) {
            return <p>No summary data available for {selectedDate}.</p>;
        }
        
        return (
            <div className="daily-summary-grid">
                <div className="daily-summary-item">
                    <span>Total Calories</span>
                    <strong>{formatValue(summary.total_calories, 0, ' kcal')}</strong>
                </div>
                <div className="daily-summary-item">
                    <span>Total Steps</span>
                    <strong>{formatValue(summary.total_steps, 0)}</strong>
                </div>
                <div className="daily-summary-item">
                    <span>Last Weight</span>
                    <strong>{formatValue(summary.last_weight_kg, 1, ' kg')}</strong>
                </div>
            </div>
        );
    };

    return (
        <div className="daily-summary-card">
            {/* Updated Header Layout */}
            <div className="daily-summary-header">
                <button onClick={goToPreviousDay} className="date-nav-button" aria-label="Previous day" disabled={loading}>{'<'}</button>
                <h4 onClick={loading ? undefined : openDatePicker} style={{ cursor: loading ? 'default' : 'pointer', margin: '0 0.5rem' }} title="Click to select date">
                    Summary for: {selectedDate}
                </h4>
                <button onClick={goToNextDay} className="date-nav-button" aria-label="Next day" disabled={loading}>{'>'}</button>
                {/* Hidden Date Input controlled by ref */}
                <input 
                    ref={dateInputRef} 
                    type="date" 
                    value={selectedDate}
                    onChange={handleDateChange}
                    aria-label="Select summary date"
                    disabled={loading} // Disable input while loading
                    style={{ 
                        position: 'absolute', 
                        left: '-9999px', 
                        opacity: 0, 
                        width: '1px',
                        height: '1px' 
                    }} 
                />
            </div>
            {renderContent()}
        </div>
    );
});

export default DailySummaryDisplay; 