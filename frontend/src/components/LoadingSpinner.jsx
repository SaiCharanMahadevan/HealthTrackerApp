import React from 'react';

/**
 * A simple CSS loading spinner component.
 * Accepts an optional 'size' prop ('small' or default/medium).
 */
function LoadingSpinner({ size = 'medium' }) { // Default size to medium
  // Determine class based on size prop
  const spinnerClass = `loading-spinner ${size === 'small' ? 'spinner-small' : ''}`;

  return (
    // Keep container for centering, but spinner itself gets size class
    <div className="spinner-container" aria-label="Loading">
      <div className={spinnerClass}></div>
    </div>
  );
}

export default LoadingSpinner; 