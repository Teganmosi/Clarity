import os
from dotenv import load_dotenv

print("--- Testing App Logic ---")
base_dir = os.path.dirname(os.path.abspath(__file__))
print(f"File __file__: {__file__}")
print(f"Absolute path: {os.path.abspath(__file__)}")

# This mimics the logic in backend/app/main.py and integrations.py
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', '.env')
print(f"Calculated env_path (if run from root): {env_path}")

# Actually, in the app, it is:
# os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
# If run from backend/app/main.py:
# dirname(abspath(__file__)) -> backend/app
# dirname(dirname(abspath(__file__))) -> backend
# join(..., '.env') -> backend/.env

# Let's test EXACTLY what's in main.py but adjusted for this script's location (root)
script_dir = os.path.dirname(os.path.abspath(__file__))
# If this script is at root, and main.py is at backend/app/main.py
main_py_simulated_path = os.path.join(script_dir, 'backend', 'app', 'main.py')
env_path_simulated = os.path.join(os.path.dirname(os.path.dirname(main_py_simulated_path)), '.env')
print(f"Simulated env_path from main.py: {env_path_simulated}")

load_dotenv(dotenv_path=env_path_simulated)
key = os.getenv("HUBSPOT_API_KEY")
print(f"HUBSPOT_API_KEY: {key[:5] if key else 'None'}...")

if not key:
    print("FAILED to load key. Checking if file exists...")
    if os.path.exists(env_path_simulated):
        print(f"File EXISTS at {env_path_simulated}")
        with open(env_path_simulated, 'r') as f:
            content = f.read()
            print(f"File content length: {len(content)}")
            print(f"Contains HUBSPOT_API_KEY: {'HUBSPOT_API_KEY' in content}")
    else:
        print(f"File DOES NOT EXIST at {env_path_simulated}")
