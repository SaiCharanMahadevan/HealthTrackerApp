import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import dayjs from 'dayjs';

const EntryForm = ({ onEntryAdded, entryToEdit = null, onSuccess, onCancel }) => {
  const [text, setText] = useState('');
  const [entryDate, setEntryDate] = useState(dayjs().format('YYYY-MM-DD'));
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    if (entryToEdit) {
      setText(entryToEdit.entry_text || '');
      setEntryDate(dayjs(entryToEdit.timestamp).format('YYYY-MM-DD'));
      setImageFile(null);
      setImagePreview(null);
      setError(null);
    } else {
      setText('');
      setEntryDate(dayjs().format('YYYY-MM-DD'));
      setImageFile(null);
      setImagePreview(null);
      setError(null);
    }
  }, [entryToEdit]);

  const handleImageChange = (event) => {
    const file = event.target.files[0];
    if (file) {
        setImageFile(file);
        const reader = new FileReader();
        reader.onloadend = () => {
            setImagePreview(reader.result);
        };
        reader.readAsDataURL(file);
    } else {
        setImageFile(null);
        setImagePreview(null);
    }
  };

  const clearImage = () => {
      setImageFile(null);
      setImagePreview(null);
      const fileInput = document.getElementById('entry-image');
      if(fileInput) fileInput.value = null;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!text.trim() && !imageFile && !entryToEdit) {
      setError('Please enter log text or upload an image.');
      return;
    }
    if (entryToEdit && !text.trim()) {
        setError('Entry text cannot be empty when editing.');
        return;
    }

    setLoading(true);
    setError(null);

    try {
      if (entryToEdit) {
        const updateData = { 
            entry_text: text,
            target_date_str: entryDate
        };
        console.log(`EntryForm: Updating entry ${entryToEdit.id} with`, updateData);
        await apiService.updateEntry(entryToEdit.id, updateData, token);
        console.log(`EntryForm: Update successful for entry ${entryToEdit.id}`);
        onSuccess();
      } else {
        const entryData = { 
          entry_text: text,
          target_date_str: entryDate
        };
        console.log("EntryForm: Adding new entry with data:", entryData, "Image:", imageFile ? imageFile.name : "None");
        await apiService.addEntry(entryData, token, imageFile); 
        console.log("EntryForm: Add successful");
        onSuccess();
      }

    } catch (err) {
      console.error('EntryForm submission error:', err);
      setError(err.message || 'Failed to save entry.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group entry-form-date-picker">
        <label htmlFor="entry-date">Entry Date:</label>
        <input 
          type="date" 
          id="entry-date"
          value={entryDate}
          onChange={(e) => setEntryDate(e.target.value)}
          max={dayjs().format('YYYY-MM-DD')}
          required 
          disabled={loading}
          className="form-input"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="entry-text">Log Text {entryToEdit ? '(Required)' : '(Optional if uploading image)'}:</label>
        <textarea
          id="entry-text"
          rows="3"
          placeholder="Log your food, weight, or steps..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={loading}
          required={!!entryToEdit}
        />
      </div>
      
      {!entryToEdit && (
        <div className="form-group">
          <label htmlFor="entry-image">Upload Food Image (Optional):</label>
          <input 
            type="file" 
            id="entry-image"
            accept="image/*"
            onChange={handleImageChange}
            disabled={loading}
            className="form-input"
          />
        </div>
      )}

      {!entryToEdit && imagePreview && (
          <div className="image-preview-container">
              <img src={imagePreview} alt="Selected preview" className="image-preview" />
              <button type="button" onClick={clearImage} disabled={loading} className="button-cancel button-small">Clear Image</button>
          </div>
      )}
      
      {error && <p className="error-message">{error}</p>}
      
      <div className="form-actions" style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
         <button type="button" onClick={onCancel} disabled={loading} className="form-button">
            Cancel
         </button>
         <button type="submit" className="form-button" disabled={loading}>
            {loading ? <LoadingSpinner size="small" /> : (entryToEdit ? 'Update Entry' : 'Log Entry')}
         </button>
      </div>
    </form>
  );
};

export default EntryForm; 