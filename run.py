import subprocess
import sys
import time
import os

def run_backend():
    print("Starting FastAPI backend...")
    # Using uvicorn to run the backend application
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        env=env
    )

def run_frontend():
    print("Starting Streamlit frontend...")
    # Using streamlit to run the frontend application
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py"],
        env=env
    )

if __name__ == "__main__":
    backend_process = None
    frontend_process = None
    try:
        backend_process = run_backend()
        # Give backend a moment to start
        time.sleep(2)
        frontend_process = run_frontend()
        
        # Keep the main thread alive
        backend_process.wait()
        frontend_process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down services...")
    finally:
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("Services stopped.")
