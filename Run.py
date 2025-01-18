from Initialize_db import initialize_session_data
import multiprocessing
from Server2 import app as lion_app
from Server3 import app as owl_app
from Server4 import app as tusk_app

def run_lion_server():
    lion_app.run(debug=False, port=5000, use_reloader=False)

def run_owl_server():
    owl_app.run(debug=False, port=5001, use_reloader=False)

def run_tusk_server():
    tusk_app.run(debug=False, port=5002, use_reloader=False)

def main():
    multiprocessing.freeze_support()
    
    # Step 1: Initialize session data
    db_path = initialize_session_data()
    print(f"Session data initialized at: {db_path}")
    
    # Step 2: Create processes for each server
    lion_process = multiprocessing.Process(target=run_lion_server)
    owl_process = multiprocessing.Process(target=run_owl_server)
    tusk_process = multiprocessing.Process(target=run_tusk_server)
    
    try:
        # Start all servers
        print("Starting Lion server on port 5000...")
        lion_process.start()
        
        print("Starting Owl server on port 5001...")
        owl_process.start()
        
        print("Starting Tusk server on port 5002...")
        tusk_process.start()
        
        # Wait for all servers
        lion_process.join()
        owl_process.join()
        tusk_process.join()
        
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        lion_process.terminate()
        owl_process.terminate()
        tusk_process.terminate()
        lion_process.join()
        owl_process.join()
        tusk_process.join()
        print("Servers shut down successfully")
    
if __name__ == "__main__":
    main()