# HealthTracker Application

A full-stack web application for tracking health and fitness metrics using natural language input and image recognition, powered by AI.

## Overview

This application allows users to log various health-related activities, meals, and measurements. It uses Google's Gemini language model to parse natural language entries and automatically extracts structured data, including nutritional information for food items (leveraging Open Food Facts where available). Users can view daily and weekly summaries, track trends over time, and manage their entries.

## Features

*   **Goal:** Log food, weight, steps (text/image). View summaries & trends.
*   **Tech:** React Frontend, Python/FastAPI Backend, PostgreSQL DB, Google Gemini AI. Deployed on Render.
*   **Key Features:**
    *   User Signup/Login
    *   Diary Page: Add/Edit/Delete entries via modal. View daily summary & entry list.
    *   Reports Page: View weekly averages & trends charts.
    *   AI Parsing: Extracts food, weight, steps. Estimates nutrition (with OFF fallback).
    *   Image Handling: Upload & auto-delete after processing.
*   **Status:** Deployed. Ongoing UI/AI refinements.

## Technology Stack

*   Backend: FastAPI (Python)
*   Frontend: React (JavaScript) with Vite
*   Database: PostgreSQL (Deployed on Render)
*   AI Model: Google Gemini (1.5 Pro / 1.5 Flash)
*   ORM: SQLAlchemy
*   Deployment: Render.com

## Setup and Running

This project is organized into two main directories:

*   `frontend/`: Contains the React single-page application.
*   `backend/`: Contains the FastAPI API server.

Each directory (`frontend/` and `backend/`) has its own specific `README.md` file with detailed instructions for local setup, including:

*   Installing dependencies
*   Configuring environment variables (e.g., API keys, database connections for the backend)
*   Running the development server

**Please refer to the `README.md` file within each respective directory (`frontend/README.md` and `backend/README.md`) to run the application locally.**

*(TODO: Add instructions for setting up the backend and frontend, including environment variables, dependencies, database creation, and run commands)* 