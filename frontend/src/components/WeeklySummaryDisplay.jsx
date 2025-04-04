import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback } from 'react';
import apiService from '../services/api';
import useAuth from '../hooks/useAuth';

const formatValue = (value, decimals = 1) => {
    if (value === null || value === undefined) return 'N/A';
    return parseFloat(value).toFixed(decimals);
};

const WeeklySummaryDisplay = forwardRef((props, ref) => {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { token } = useAuth();

    const fetchSummary = useCallback(async () => {
        if (!token) return;
        setLoading(true);
        setError(null);
        try {
            const data = await apiService.getWeeklySummary(token);
            setSummary(data);
        } catch (err) {
            setError(err.message || 'Failed to fetch weekly summary.');
            console.error(err);
            setSummary(null);
        } finally {
            setLoading(false);
        }
    }, [token]);

    useEffect(() => {
        fetchSummary();
    }, [fetchSummary]);

    useImperativeHandle(ref, () => ({ 
        refetch: fetchSummary
    }));

    if (loading) {
        return <p>Loading weekly summary...</p>;
    }

    if (error) {
        return <p className="error-message">Error: {error}</p>;
    }

    if (!summary) {
        return <p>No weekly summary data available.</p>;
    }

    return (
        <div className="summary-card"> 
            <h3>Week: {summary.week_start_date} to {summary.week_end_date}</h3>
            <div className="summary-grid">
                <div><strong>Avg Calories:</strong> {formatValue(summary.avg_daily_calories, 0)} kcal/day</div>
                <div><strong>Avg Protein:</strong> {formatValue(summary.avg_daily_protein_g, 1)} g/day</div>
                <div><strong>Avg Carbs:</strong> {formatValue(summary.avg_daily_carbs_g, 1)} g/day</div>
                <div><strong>Avg Fat:</strong> {formatValue(summary.avg_daily_fat_g, 1)} g/day</div>
                <div><strong>Avg Weight:</strong> {formatValue(summary.avg_weight_kg, 1)} kg</div>
                <div><strong>Total Steps:</strong> {summary.total_steps?.toLocaleString() ?? 'N/A'}</div>
                <div><strong>Avg Steps:</strong> {formatValue(summary.avg_daily_steps, 0)} steps/day</div>
            </div>
        </div>
    );
});

export default WeeklySummaryDisplay; 