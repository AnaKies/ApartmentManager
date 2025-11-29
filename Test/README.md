# Automated CRUD Test Suite

This folder contains an automated test suite for the ApartmentManager application.
It uses Selenium for browser automation and a second LLM client (Gemini) to simulate user behavior.

## Prerequisites

1.  **Python 3.10+**
2.  **Google Chrome** installed.
3.  **Gemini API Key** in your `.env` file (in the project root).

## Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Running the Test

Run the test script from this directory:

```bash
python run_crud_test.py
```

## How it Works

1.  **Starts Backend**: Launches the Flask backend server.
2.  **Starts Frontend**: Launches a local HTTP server for the frontend.
3.  **Opens Browser**: Opens Chrome and navigates to the app.
4.  **Simulates User**:
    *   The test script defines a list of goals (Create, Read, Update, Delete).
    *   It uses a "User LLM" (Gemini) to generate natural language requests based on the goal and the current chat history.
    *   It types these requests into the chat window.
5.  **Verifies Results**:
    *   The User LLM decides when a task is "DONE".
    *   The script then checks the page DOM to verify that the expected data (e.g., created person's name) is present.

## Configuration

*   **`run_crud_test.py`**: You can modify the `tasks` list to change the test scenarios.
*   **`user_llm_client.py`**: Logic for the simulated user.
