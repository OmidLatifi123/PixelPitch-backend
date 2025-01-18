import json
import os

# Define the path to the session data file
DB_PATH = "backend/db/session_data.json"

def initialize_session_data():
    """
    Initializes the session data file if it doesn't exist.
    Returns the path to the session data file.
    """
    if not os.path.exists(DB_PATH):
        # Initial structure for session data
        session_data = {
            "lion": {"messages": [], "mood": "NEUTRAL"},
            "owl": {"messages": [], "mood": "NEUTRAL"},
            "tusk": {"messages": [], "mood": "NEUTRAL"},
        }
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        # Write initial data to the file
        with open(DB_PATH, "w") as f:
            json.dump(session_data, f)
    return DB_PATH


if __name__ == "__main__":
    # Run the function for testing
    path = initialize_session_data()
    print(f"Session data initialized at: {path}")