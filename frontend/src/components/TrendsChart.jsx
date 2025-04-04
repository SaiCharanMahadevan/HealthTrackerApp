import React, { useState, useEffect, forwardRef, useImperativeHandle, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiService from '../services/api';
import useAuth from '../hooks/useAuth';
import { formatValue, formatLocalDateTime, formatLocalDate } from '../utils/formatters';

// Format date for XAxis labels
const formatXAxis = (tickItem) => {
    // Assuming tickItem is a full ISO datetime string from the API
    try {
        return new Date(tickItem).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch (e) {
        return tickItem; // Fallback
    }
};

// Custom Tooltip Content
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        {/* Use formatLocalDate for the tooltip label */}
        <p className="label">{`${formatLocalDate(label)}`}</p>
        {payload.map((pld, index) => (
          <p key={index} style={{ color: pld.color }}>
            {`${pld.name}: ${formatValue(pld.value, 1, pld.unit || '')}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Wrap component with forwardRef
const TrendsChart = forwardRef((props, ref) => {
    const [trendData, setTrendData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { token } = useAuth();

    // Extract fetch logic into a useCallback function
    const fetchTrends = useCallback(async () => {
        if (!token) return;
        setLoading(true);
        setError(null);
        try {
            const data = await apiService.getTrends(token);
            
            // Transform data for Recharts
            const formattedWeight = data.weight_trends.map(p => ({ 
                timestamp: p.timestamp,
                date: new Date(p.timestamp).toISOString().split('T')[0],
                Weight: p.value 
            }));
            const formattedSteps = data.steps_trends.map(p => ({ 
                timestamp: p.timestamp,
                date: new Date(p.timestamp).toISOString().split('T')[0],
                Steps: p.value 
            }));

            // Combine and sort
            const combinedDataMap = new Map();
            formattedWeight.forEach(p => combinedDataMap.set(p.date, { ...combinedDataMap.get(p.date), timestamp: p.timestamp, date: p.date, Weight: p.Weight }));
            formattedSteps.forEach(p => combinedDataMap.set(p.date, { ...combinedDataMap.get(p.date), timestamp: p.timestamp, date: p.date, Steps: p.Steps }));
            const combinedData = Array.from(combinedDataMap.values()).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

            setTrendData(combinedData);

        } catch (err) {
            setError(err.message || 'Failed to fetch trend data.');
            console.error(err);
            setTrendData([]); // Clear data on error
        } finally {
            setLoading(false);
        }
    }, [token]); // Dependency: token

    // Initial fetch on mount
    useEffect(() => {
        fetchTrends();
    }, [fetchTrends]);

    // Expose the refetch function via useImperativeHandle
    useImperativeHandle(ref, () => ({ 
        refetch: fetchTrends
    }));

    if (loading) {
        return <p>Loading trend charts...</p>;
    }

    if (error) {
        return <p className="error-message">Error loading trends: {error}</p>;
    }

    if (!trendData || trendData.length === 0) {
        return <p>No trend data available for the selected period.</p>;
    }

    return (
        <div className="trends-card"> 
            <h3>Trends (Last 30 Days)</h3>
            {/* Weight Chart */}
            <h4>Weight Trend</h4>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                    <XAxis 
                        dataKey="timestamp" 
                        tickFormatter={(timestamp) => formatLocalDate(timestamp)} 
                        stroke="#aaa" 
                        angle={-30} /* Angle ticks for better fit */
                        textAnchor="end"
                        height={50} /* Increase height for angled ticks */
                    />
                    <YAxis yAxisId="left" stroke="#8884d8" label={{ value: 'Weight (kg)', angle: -90, position: 'insideLeft', fill: '#8884d8' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="Weight" stroke="#8884d8" activeDot={{ r: 8 }} name="Weight (kg)" connectNulls />
                </LineChart>
            </ResponsiveContainer>

            {/* Steps Chart */}
            <h4 style={{ marginTop: '2rem' }}>Steps Trend</h4>
            <ResponsiveContainer width="100%" height={300}>
                 <LineChart data={trendData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                    <XAxis 
                        dataKey="timestamp" 
                        tickFormatter={(timestamp) => formatLocalDate(timestamp)} 
                        stroke="#aaa" 
                        angle={-30} /* Angle ticks for better fit */
                        textAnchor="end"
                        height={50} /* Increase height for angled ticks */
                    />
                    <YAxis yAxisId="right" stroke="#82ca9d" label={{ value: 'Steps', angle: -90, position: 'insideLeft', fill: '#82ca9d' }}/>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Line yAxisId="right" type="monotone" dataKey="Steps" stroke="#82ca9d" activeDot={{ r: 8 }} name="Daily Steps" connectNulls />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
});

export default TrendsChart; 