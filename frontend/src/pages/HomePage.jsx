import React, { useState, useEffect } from 'react';
import { createHealthEntry, getHealthEntries } from '../services/api';

// Helper function to display parsed data nicely
const displayParsedData = (entry) => {
  if (!entry.entry_type || entry.entry_type === 'unknown' || entry.entry_type === 'error') {
    return <span>{entry.entry_text}</span>; // Fallback to raw text
  }

  switch (entry.entry_type) {
    case 'weight':
      return <span>Weight: {entry.value} {entry.unit}</span>;
    case 'steps':
      return <span>Steps: {entry.value}</span>;
    case 'food':
      if (entry.parsed_data && entry.parsed_data.items) {
        const items = entry.parsed_data.items.map((item, index) => (
          <span key={index}>
            {item.quantity} {item.unit || ''} {item.item} 
            ({item.calories ? `${item.calories} kcal` : 'N/A'})
            {index < entry.parsed_data.items.length - 1 ? ', ' : ''}
          </span>
        ));
        const totals = ` | Total: ${entry.parsed_data.total_calories || '?'} kcal, P:${entry.parsed_data.total_protein_g || '?'}g, C:${entry.parsed_data.total_carbs_g || '?'}g, F:${entry.parsed_data.total_fat_g || '?'}g`;
        return <span>Food: {items}{totals}</span>;
      }
      return <span>Food: (details missing) - {entry.entry_text}</span>; // Fallback if structure is wrong
    default:
      return <span>{entry.entry_text}</span>;
  }
};

function HomePage() {
  const [entryText, setEntryText] = useState('');
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(null);
  const token = localStorage.getItem('authToken'); // Get token

  // Fetch entries when component mounts or token changes
  useEffect(() => {
    const fetchEntries = async () => {
      if (!token) {
        setError('Authentication required.');
        return;
      }
      try {
        setError(null);
        const fetchedEntries = await getHealthEntries(token);
        // Sort entries by timestamp, newest first (optional)
        fetchedEntries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        setEntries(fetchedEntries);
      } catch (err) {
        setError('Failed to fetch entries.');
        console.error(err);
      }
    };

    fetchEntries();
  }, [token]); // Re-fetch if token changes

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!token || !entryText.trim()) {
        setError('Entry text cannot be empty.');
        return;
    }

    try {
      setError(null);
      const newEntry = await createHealthEntry(token, entryText);
      // Add new entry to the top of the list
      setEntries([newEntry, ...entries]); 
      setEntryText(''); // Clear input field
    } catch (err) {
      setError('Failed to save entry.');
      console.error(err);
    }
  };

  return (
    <div>
      <h1>Health Tracker Dashboard</h1>
      
      <form onSubmit={handleSubmit} className="entry-form">
        <textarea 
            rows="3"
            cols="50"
            value={entryText}
            onChange={(e) => setEntryText(e.target.value)}
            placeholder="Log your food, weight, or steps (e.g., 'Today I ate 2 eggs and ran 5km', 'Weight 80.5 kg')"
            required
        />
        <br />
        <button type="submit">Log Entry</button>
      </form>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <h2>Recent Entries</h2>
      {entries.length > 0 ? (
        <ul className="entry-list">
          {entries.map((entry) => (
            <li key={entry.id}>
              <strong>{new Date(entry.timestamp).toLocaleString()}:</strong> 
              {displayParsedData(entry)}
            </li>
          ))}
        </ul>
      ) : (
        <p>No entries yet. Add one above!</p>
      )}
    </div>
  );
}

export default HomePage; 