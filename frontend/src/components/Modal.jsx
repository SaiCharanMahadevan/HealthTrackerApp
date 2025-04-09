import React from 'react';
import ReactDOM from 'react-dom';

function Modal({ children, onClose, title = 'Modal' }) {
  // Use createPortal to render the modal outside of the parent component's DOM hierarchy
  // This helps with stacking context and positioning
  return ReactDOM.createPortal(
    <div className="modal-overlay" onClick={onClose}> {/* Close on overlay click */} 
      <div className="modal-content" onClick={e => e.stopPropagation()}> {/* Prevent closing when clicking inside content */} 
        {title && <h2 className="modal-header">{title}</h2>}
        <button className="modal-close-button" onClick={onClose} aria-label="Close modal">&times;</button>
        {children}
      </div>
    </div>,
    document.getElementById('modal-root') || document.body // Render into a specific div if exists, else body
  );
}

export default Modal; 