import React, { useState, useRef, useEffect } from 'react';
import EntryForm from '../components/EntryForm';
import EntryList from '../components/EntryList';
import DailySummaryDisplay from '../components/DailySummaryDisplay';
import Modal from '../components/Modal';
import {useAuth} from '../contexts/AuthContext';
import apiService from '../services/api';

function DiaryPage() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(null);
  const { token } = useAuth();
  
  const entryListRef = useRef(null);
  const dailySummaryRef = useRef(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [entryToEdit, setEntryToEdit] = useState(null);

  const handleOpenAddModal = () => {
    setEntryToEdit(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (entry) => {
    setEntryToEdit(entry);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEntryToEdit(null);
  };

  const handleSaveSuccess = () => {
    handleCloseModal();
    entryListRef.current?.refetch();
    dailySummaryRef.current?.refetch();
  };

  const handleEntryDeleted = (deletedEntryId) => {
    setEntries(prevEntries => prevEntries.filter(entry => entry.id !== deletedEntryId));
    dailySummaryRef.current?.refetch();
  };

  const handleEntryUpdated = (updatedEntry) => {
    dailySummaryRef.current?.refetch();
  };

  useEffect(() => {
    const fetchEntries = async () => {
      if (!token) return;
      try {
        const fetchedEntries = await apiService.getEntries(token);
        fetchedEntries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        setEntries(fetchedEntries);
      } catch (err) {
        console.error("Failed to fetch entries on DiaryPage:", err);
      }
    };
    fetchEntries();
  }, [token]);

  return (
    <div className="page-container diary-page">
      <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
        <button onClick={handleOpenAddModal} className="form-button" style={{width: 'auto', padding: '0.8rem 1.5rem'}}>
          Add New Log Entry
        </button>
      </div>

      <DailySummaryDisplay ref={dailySummaryRef} />

      <div className="view-entry-section">
        <h2>Logged Entries</h2>
        {error && <p className="error-message">{error}</p>}
        <EntryList
          ref={entryListRef}
          entries={entries}
          setEntries={setEntries}
          onEntryDeleted={handleEntryDeleted}
          onEntryUpdated={handleEntryUpdated}
          onEditClick={handleOpenEditModal}
        />
      </div>

      {isModalOpen && (
        <Modal onClose={handleCloseModal} title={entryToEdit ? "Edit Entry" : "Add New Entry"}>
          <EntryForm
            entryToEdit={entryToEdit}
            onSuccess={handleSaveSuccess}
            onCancel={handleCloseModal}
          />
        </Modal>
      )}
    </div>
  );
}

export default DiaryPage; 