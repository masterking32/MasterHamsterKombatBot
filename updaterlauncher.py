import os
import sys
import subprocess
import time
import requests

# Constants
GITHUB_RAW_URL = "https://raw.githubusercontent.com/tboy1337/MasterHamsterKombatBot/test/"
LAUNCHER_SCRIPT_NAME = "updaterlauncher.py"
UPDATER_SCRIPT_NAME = "updater.py"
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory
UPDATER_SCRIPT_PATH = os.path.join(CURRENT_DIR, UPDATER_SCRIPT_NAME)  # Full path to updater.py
LAUNCHER_SCRIPT_PATH = os.path.join(CURRENT_DIR, LAUNCHER_SCRIPT_NAME)  # Full path to updaterlauncher.py

def get_github_file_contents(url):
    """Fetches the content of a file from a given GitHub URL."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error fetching file from GitHub: {url} - Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching file from GitHub: {e}")
        return None

def restart_updater():
    """Restarts the updater.py script in a new command window."""
    print("Attempting to restart updater.py in a new command window...")
    python_executable = f'"{sys.executable}"'
    command = f'start cmd /c {python_executable} "{UPDATER_SCRIPT_PATH}"'
    print(f"Executing command: {command}")
    subprocess.Popen(command, shell=True)
    print("Command executed, exiting launcher.")
    sys.exit(0)  # Exit the current instance of updaterlauncher.py

def self_update():
    """Checks if the launcher script or updater.py needs to be updated and performs the update if necessary."""
    updated = False
    
    # Update updaterlauncher.py
    github_launcher_contents = get_github_file_contents(GITHUB_RAW_URL + LAUNCHER_SCRIPT_NAME)
    if github_launcher_contents:
        with open(LAUNCHER_SCRIPT_PATH, 'r', encoding='utf-8') as file:
            local_launcher_contents = file.read()
        if github_launcher_contents != local_launcher_contents:
            print("Launcher script is outdated. Updating...")
            with open(LAUNCHER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
                file.write(github_launcher_contents)
            updated = True

    # Update updater.py
    github_updater_contents = get_github_file_contents(GITHUB_RAW_URL + UPDATER_SCRIPT_NAME)
    if github_updater_contents:
        with open(UPDATER_SCRIPT_PATH, 'r', encoding='utf-8') as file:
            local_updater_contents = file.read()
        if github_updater_contents != local_updater_contents:
            print("Updater script is outdated. Updating...")
            with open(UPDATER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
                file.write(github_updater_contents)
            updated = True

    if updated:
        print("Updates applied. Restarting updater.py...")
        restart_updater()

def launch_updater():
    """Launches the updater.py script in a new command window."""
    print("Attempting to launch updater.py in a new command window...")
    python_executable = f'"{sys.executable}"'
    command = f'start "" {python_executable} "{UPDATER_SCRIPT_PATH}"'
    print(f"Executing command: {command}")
    subprocess.Popen(command, shell=True)
    print("Command executed.")


if __name__ == "__main__":
    print("Launcher started.")
    self_update()  # Check if the launcher or updater.py needs to be updated
    launch_updater()  # Start the updater script
    while True:
        time.sleep(10)  # Keep the launcher running
