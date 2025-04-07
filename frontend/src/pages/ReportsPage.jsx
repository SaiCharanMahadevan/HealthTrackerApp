import React, { useState, useEffect } from 'react';
import WeeklySummaryDisplay from '../components/WeeklySummaryDisplay'; // Assuming this exists
import TrendsChart from '../components/TrendsChart';
import apiService from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner'; // Import spinner

function ReportsPage() {
    const { token } = useAuth();
    const [weeklySummary, setWeeklySummary] = useState(null);
    const [trendsData, setTrendsData] = useState(null); // Default to null initially
    const [loadingWeekly, setLoadingWeekly] = useState(false);
    const [loadingTrends, setLoadingTrends] = useState(false);
    const [errorWeekly, setErrorWeekly] = useState(null);
    const [errorTrends, setErrorTrends] = useState(null);

    // Fetch Weekly Summary Data
    useEffect(() => {
        if (!token) return;
        setLoadingWeekly(true);
        setErrorWeekly(null);
        apiService.getWeeklySummary(token)
            .then(data => setWeeklySummary(data))
            .catch(err => {
                console.error("ReportsPage: Weekly summary fetch error:", err);
                setErrorWeekly(err.message || 'Failed to load weekly summary');
            })
            .finally(() => setLoadingWeekly(false));
    }, [token]);

    // Fetch Trends Data 
    useEffect(() => {
        if (!token) return;
        setLoadingTrends(true);
        setErrorTrends(null);
        // Pass null/undefined for default range, or specific dates if adding date pickers here
        apiService.getTrends(token, null, null) 
            .then(data => setTrendsData(data))
            .catch(err => {
                console.error("ReportsPage: Trends fetch error:", err);
                setErrorTrends(err.message || 'Failed to load trends');
            })
            .finally(() => setLoadingTrends(false));
    }, [token]);

    return (
        <div className="page-container reports-page">
            <h2>Reports</h2>

            {/* Weekly Summary Section */}
            <div className="report-section weekly-summary-section">
                <h3>Weekly Summary</h3>
                {/* Show spinner or content */}
                {loadingWeekly ? <LoadingSpinner /> : (
                    errorWeekly ? <p className="error-message">{errorWeekly}</p> : (
                        weeklySummary ? <WeeklySummaryDisplay summary={weeklySummary} /> : <p>No weekly data.</p>
                    )
                )}
            </div>

            {/* Trends Section */}
            <div className="report-section trends-section">
                {/* Pass trendsData directly - TrendsChart handles internal loading/error display based on props */}
                 <TrendsChart trendData={trendsData} loading={loadingTrends} error={errorTrends} />
                 {/* Alternative if TrendsChart doesn't handle loading/error: */} 
                 {/*
                 <h3>Trends</h3>
                 {loadingTrends ? <LoadingSpinner /> : (
                     errorTrends ? <p className="error-message">{errorTrends}</p> : (
                         trendsData ? <TrendsChart trendData={trendsData} /> : <p>No trend data.</p>
                     )
                 )}
                 */}
            </div>

        </div>
    );
}

export default ReportsPage; 