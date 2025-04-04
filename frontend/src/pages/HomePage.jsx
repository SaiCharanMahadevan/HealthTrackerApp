import React, { useState, useRef } from 'react';
import useAuth from '../hooks/useAuth';
import EntryInput from '../components/EntryInput';
import EntryList from '../components/EntryList';
import WeeklySummaryDisplay from '../components/WeeklySummaryDisplay';
import TrendsChart from '../components/TrendsChart';
import DailySummaryDisplay from '../components/DailySummaryDisplay';

const HomePage = () => {
    const { logout, user } = useAuth();
    const [entries, setEntries] = useState([]);

    // Create refs for report components
    const summaryRef = useRef();
    const trendsRef = useRef();
    const dailySummaryRef = useRef();

    const triggerReportRefetch = () => {
        summaryRef.current?.refetch();
        trendsRef.current?.refetch();
        dailySummaryRef.current?.refetch();
    };

    const handleEntryAdded = (newEntry) => {
        setEntries(prevEntries => [newEntry, ...prevEntries]);
        triggerReportRefetch(); // Trigger refetch
    };

    // Callback for EntryList to update the state after successful edit
    const handleEntryUpdated = (updatedEntry) => {
        setEntries(prevEntries => prevEntries.map(entry => 
            entry.id === updatedEntry.id ? updatedEntry : entry
        ));
        triggerReportRefetch(); // Trigger refetch
    };

    // Callback for EntryList to update the state after successful delete
    const handleEntryDeleted = (deletedEntryId) => {
        setEntries(prevEntries => prevEntries.filter(entry => entry.id !== deletedEntryId));
        triggerReportRefetch(); // Trigger refetch
    };

    return (
        <div className="home-page-container">
            <header className="home-header">
                <h1>Health Tracker</h1>
                <div className="user-info">
                    {user && <span>Welcome, {user.email}!</span>} 
                    <button onClick={logout}>Logout</button>
                </div>
            </header>
            
            <section className="reports-section">
                <h2>Reports</h2>
                <DailySummaryDisplay ref={dailySummaryRef} />
                <div className="reports-grid" style={{marginTop: '2rem'}}>
                    <WeeklySummaryDisplay ref={summaryRef} />
                    <TrendsChart ref={trendsRef} />
                </div>
            </section>

            <main className="home-main-content">
                <section className="log-entry-section">
                    <h2>Log your health data:</h2>
                    <EntryInput onEntryAdded={handleEntryAdded} />
                </section>
                
                <section className="view-entry-section">
                    <h2>Your Entries:</h2>
                    <EntryList 
                        entries={entries} 
                        setEntries={setEntries} 
                        onEntryUpdated={handleEntryUpdated}
                        onEntryDeleted={handleEntryDeleted}
                    />
                </section>
            </main>
        </div>
    );
};

export default HomePage; 