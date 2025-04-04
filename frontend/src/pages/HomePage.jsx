import React, { useState } from 'react';
import useAuth from '../hooks/useAuth';
import EntryInput from '../components/EntryInput';
import EntryList from '../components/EntryList';
import WeeklySummaryDisplay from '../components/WeeklySummaryDisplay';
import TrendsChart from '../components/TrendsChart';

const HomePage = () => {
    const { logout, user } = useAuth();
    const [entries, setEntries] = useState([]);

    const handleEntryAdded = (newEntry) => {
        setEntries(prevEntries => [newEntry, ...prevEntries]);
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
                <div className="reports-grid">
                    <WeeklySummaryDisplay />
                    <TrendsChart />
                </div>
            </section>

            <main className="home-main-content">
                <section className="log-entry-section">
                    <h2>Log your health data:</h2>
                    <EntryInput onEntryAdded={handleEntryAdded} />
                </section>
                
                <section className="view-entry-section">
                    <h2>Your Entries:</h2>
                    <EntryList entries={entries} setEntries={setEntries} />
                </section>
            </main>
        </div>
    );
};

export default HomePage; 