from Initialize_db import initialize_session_data
from Server import app

def main():
    # Step 1: Initialize session data
    db_path = initialize_session_data()
    print(f"Session data initialized at: {db_path}")
    
    # Step 2: Run the Flask server
    app.run(debug=True)

if __name__ == "__main__":
    main()