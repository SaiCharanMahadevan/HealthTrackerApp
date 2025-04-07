import React, { useState, useRef, useEffect } from 'react';
import EntryForm from '../components/EntryForm';
import EntryList from '../components/EntryList';
import DailySummaryDisplay from '../components/DailySummaryDisplay';
import apiService from '../services/api';
import {useAuth} from '../contexts/AuthContext';

function DiaryPage() {
  const [entries, setEntries] = useState([]);
  const { token } = useAuth();
  const dailySummaryRef = useRef(null);
  // Note: EntryList fetches its own data initially, but we need to update it
  // when an entry is added/deleted/updated via EntryForm or EntryList itself.

  // Function to be called by EntryForm/EntryList after modification
  const handleEntryUpdate = (updatedEntry) => {
    setEntries(prevEntries => 
      prevEntries.map(entry => (entry.id === updatedEntry.id ? updatedEntry : entry))
    );
    // Also refetch daily summary in case the update affects it
    dailySummaryRef.current?.refetch();
  };

  const handleEntryDelete = (deletedEntryId) => {
    setEntries(prevEntries => 
      prevEntries.filter(entry => entry.id !== deletedEntryId)
    );
    // Refetch daily summary
    dailySummaryRef.current?.refetch();
  };
  
  const handleEntryAdded = (newEntry) => {
     // Add to top of list for immediate feedback, assuming EntryList sorts later
    setEntries(prevEntries => [newEntry, ...prevEntries]); 
    // Refetch daily summary
    dailySummaryRef.current?.refetch();
  }

  // Initial fetch for EntryList (moved from EntryList useEffect for consistency)
   useEffect(() => {
    const fetchEntries = async () => {
      if (!token) return;
      try {
        const fetchedEntries = await apiService.getEntries(token);
        // Sort entries by timestamp descending
        fetchedEntries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        setEntries(fetchedEntries);
      } catch (err) {
        console.error("Failed to fetch entries on DiaryPage:", err);
        // Handle error display if needed
      }
    };
    fetchEntries();
  }, [token]); // Fetch when token changes

  return (
    <div className="page-container diary-page">
      <h2>Diary</h2>
      
      <EntryForm onEntryAdded={handleEntryAdded} />
      
      <DailySummaryDisplay ref={dailySummaryRef} />

      <EntryList 
        entries={entries} 
        setEntries={setEntries} // Pass down state setter if EntryList needs to modify (e.g., delete/edit internal state)
        onEntryUpdated={handleEntryUpdate} // Callback for updates within EntryList
        onEntryDeleted={handleEntryDelete} // Callback for deletes within EntryList
      />

      {/* Removed WeeklySummary and TrendsChart */}
    </div>
  );
}

export default DiaryPage; 