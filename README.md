# HealthTracker Application

A full-stack web application for tracking health and fitness metrics using natural language input and image recognition, powered by AI.

## Overview

This application allows users to log various health-related activities, meals, and measurements. It uses Google's Gemini language model to parse natural language entries and automatically extracts structured data, including nutritional information for food items (leveraging Open Food Facts where available). Users can view daily and weekly summaries, track trends over time, and manage their entries.

## Features

*   **User Authentication:** Secure user registration (signup), login, and logout.
*   **Natural Language Entry:** Log food, weight, and steps using plain text (e.g., "had 2 eggs and toast", "weight 80kg", "walked 5000 steps").
*   **Image-Based Food Logging:** Upload an image of a meal for automatic food item identification and nutritional estimation.
*   **AI-Powered Parsing:** Utilizes Google Gemini (1.5 Pro) for multimodal analysis of text and images to extract structured health data (type, value, unit, nutritional info).
*   **Open Food Facts Integration:** Enhances nutritional data accuracy for recognized food items.
*   **Diary View:**
    *   Daily Summary: Displays total calories, total steps, and last recorded weight for a selected date.
    *   Date Navigation: Easily navigate between daily summaries (previous/next day buttons, date picker).
    *   Entry Form: Input text or upload images for logging.
    *   Backdating: Log entries for past dates.
    *   Entry List: View a chronological list of logged entries with edit and delete capabilities.
*   **Reports View:**
    *   Weekly Summary: Provides averages for calories, macronutrients, steps, and weight over a week.
    *   Trend Charts: Visualizes weight and step trends over time.
*   **Timezone Awareness:** Summaries and reports are calculated based on the user's local timezone.
*   **Technology Stack:**
    *   Backend: FastAPI (Python)
    *   Frontend: React (JavaScript)
    *   Database: SQLite
    *   AI Model: Google Gemini
    *   OR M: SQLAlchemy

## Setup and Running

*(TODO: Add instructions for setting up the backend and frontend, including environment variables, dependencies, database creation, and run commands)* 