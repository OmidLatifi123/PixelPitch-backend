from Initialize_db import initialize_session_data
import multiprocessing
from Server2 import app as lion_app
from Server3 import app as owl_app
from Server4 import app as tusk_app
from Server5 import app as summary_app
from authServer import app as auth_app

def run_lion_server():
    lion_app.run(debug=True, port=5000, use_reloader=False)

def run_owl_server():
    owl_app.run(debug=True, port=5001, use_reloader=False)

def run_tusk_server():
    tusk_app.run(debug=True, port=5002, use_reloader=False)

def run_auth_server():
    auth_app.run(debug=True,port=5003,use_reloader=False)

def run_summary_server():
    summary_app.run(debug=True, port=5004, use_reloader=False)

def main():
    multiprocessing.freeze_support()
    
    # Step 1: Initialize session data
    db_path = initialize_session_data()
    print(f"Session data initialized at: {db_path}")
    
    # Step 2: Create processes for each server
    lion_process = multiprocessing.Process(target=run_lion_server)
    owl_process = multiprocessing.Process(target=run_owl_server)
    tusk_process = multiprocessing.Process(target=run_tusk_server)
    summary_process = multiprocessing.Process(target=run_summary_server)
    auth_process= multiprocessing.Process(target=run_auth_server)
    
    try:
        # Start all servers
        print("Starting Lion server on port 5000...")
        lion_process.start()
        
        print("Starting Owl server on port 5001...")
        owl_process.start()
        
        print("Starting Tusk server on port 5002...")
        tusk_process.start()

        print("Starting auth server on port 5003...")
        auth_process.start()

        print("Starting auth server on port 5004...")
        summary_process.start()
        
        # Wait for all servers
        lion_process.join()
        owl_process.join()
        tusk_process.join()
        auth_process.join()
        summary_process.join()

    except KeyboardInterrupt:
        print("\nShutting down servers...")
        lion_process.terminate()
        owl_process.terminate()
        tusk_process.terminate()
        auth_process.terminate()
        summary_process.terminate()
        lion_process.join()
        owl_process.join()
        tusk_process.join()
        auth_process.join()
        summary_process.join()
        print("Servers shut down successfully")
    
if __name__ == "__main__":
    main()