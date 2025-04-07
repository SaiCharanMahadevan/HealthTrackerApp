import React, { useState } from 'react';
import apiService from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';
import dayjs from 'dayjs';

const EntryForm = ({ onEntryAdded }) => {
  const [text, setText] = useState('');
  const [entryDate, setEntryDate] = useState(dayjs().format('YYYY-MM-DD'));
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { token } = useAuth();

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
    if ((!text || !text.trim()) && !imageFile) {
      setError('Please enter text or select an image.');
      return;
    }
    if (!token) {
        setError('Authentication error.');
        return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload = { 
          entry_text: text, 
          target_date_str: entryDate 
      };
      const newEntry = await apiService.addEntry(payload, token, imageFile);
      onEntryAdded(newEntry);
      setText('');
      clearImage();
    } catch (err) {
      console.error("Add entry failed:", err);
      setError(err.message || 'Failed to add entry.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="entry-form-card">
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
          <label htmlFor="entry-text">Log Text (Optional if uploading image):</label>
          <textarea
            id="entry-text"
            rows="3"
            placeholder="Log your food, weight, or steps (e.g., '1 apple and 1 banana', 'Weight 80 kg', '10000 steps today')"
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
            required
          />
        </div>
        
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

        {imagePreview && (
            <div className="image-preview-container">
                <img src={imagePreview} alt="Selected preview" className="image-preview" />
                <button type="button" onClick={clearImage} disabled={loading} className="button-cancel button-small">Clear Image</button>
            </div>
        )}
        
        <button type="submit" className="form-button" disabled={loading}>
          {loading ? <LoadingSpinner size="small" /> : 'Log Entry'}
        </button>
        {error && <p className="error-message">{error}</p>}
      </form>
    </div>
  );
};

export default EntryForm; 