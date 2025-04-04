import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone'; // For timezone conversion
import localizedFormat from 'dayjs/plugin/localizedFormat'; // For locale-aware formats like 'L LT'

// Extend dayjs with the necessary plugins
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(localizedFormat);

/**
 * Formats a UTC ISO 8601 date string into a locale-aware date and time string using dayjs.
 * Example: "2023-10-27T10:30:00Z" might become "10/27/2023, 6:30 AM" (depending on locale/timezone).
 * 
 * @param {string | null | undefined} isoString The UTC ISO 8601 date string.
 * @returns {string} The formatted local date and time string, or 'Invalid Date'/'N/A'.
 */
export const formatLocalDateTime = (isoString) => {
  if (!isoString) {
    return 'N/A'; // Handle null or undefined input
  }
  try {
    // Parse the UTC string and convert it to the local timezone
    const date = dayjs.utc(isoString).local(); 
    
    // Check if the date is valid
    if (!date.isValid()) {
      return 'Invalid Date';
    }
    
    // Format using a locale-aware format (e.g., 'L LT' -> 'MM/DD/YYYY h:mm A')
    // You can explore other formats provided by localizedFormat: 
    // https://day.js.org/docs/en/plugin/localized-format
    return date.format('L LT'); 

  } catch (error) {
    console.error("Error formatting date with dayjs:", isoString, error);
    return 'Invalid Date'; // Return an error indicator
  }
};

/**
 * Formats a UTC ISO 8601 date string into a locale-aware date string (no time) using dayjs.
 * Example: "2023-10-27T10:30:00Z" might become "10/27/2023" (depending on locale).
 * 
 * @param {string | null | undefined} isoString The UTC ISO 8601 date string.
 * @returns {string} The formatted local date string, or 'Invalid Date'/'N/A'.
 */
export const formatLocalDate = (isoString) => {
  if (!isoString) {
    return 'N/A';
  }
  try {
    // Parse UTC, convert to local, check validity
    const date = dayjs.utc(isoString).local(); 
    if (!date.isValid()) {
      return 'Invalid Date';
    }
    // Format using 'L' (locale-specific date format, e.g., MM/DD/YYYY)
    return date.format('L'); 
  } catch (error) {
    console.error("Error formatting date-only with dayjs:", isoString, error);
    return 'Invalid Date';
  }
};

/**
 * Formats a value nicely, handling null/undefined and adding optional suffix.
 * 
 * @param {number | string | null | undefined} value The value to format.
 * @param {number} decimals Maximum number of decimal places.
 * @param {string} suffix Optional suffix (e.g., ' kg', ' kcal').
 * @returns {string} Formatted string or 'N/A'.
 */
export const formatValue = (value, decimals = 1, suffix = '') => {
    if (value === null || value === undefined) return 'N/A';
    const number = parseFloat(value);
    return isNaN(number) ? 'N/A' : `${number.toLocaleString(undefined, {maximumFractionDigits: decimals})}${suffix}`;
}; 