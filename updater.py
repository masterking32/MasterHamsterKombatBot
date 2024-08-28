import os
import sys
import requests
import time
import psutil
import subprocess
import json

# Constants
GITHUB_RAW_URL = "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/"
FILES_CONFIG_URL = GITHUB_RAW_URL + "files_to_update.json"
UPDATER_SCRIPT_NAME = "updater.py"
CHECK_DELAY = 60  # Delay in seconds between each update check cycle
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory of the updater script
MAIN_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'main.py')  # Full path to main.py
UPDATER_SCRIPT_PATH = os.path.join(CURRENT_DIR, UPDATER_SCRIPT_NAME)  # Full path to updater.py

def get_local_file_contents(file_path):
    """Reads the content of a local file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File {file_path} not found. It will be downloaded.")
        return None
    except UnicodeDecodeError as e:
        print(f"Error reading local file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"General error reading local file {file_path}: {e}")
        return None

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

def fetch_file_list():
    """Fetches the list of files to update from files_to_update.json on GitHub."""
    config_contents = get_github_file_contents(FILES_CONFIG_URL)
    if config_contents is None:
        print("Failed to fetch the list of files to update.")
        return []
    try:
        file_list = json.loads(config_contents)
        return file_list.get("files", [])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from file list: {e}")
        return []

def update_file(file_name, github_url):
    """Downloads and updates a local file from GitHub if necessary."""
    github_contents = get_github_file_contents(github_url)
    if github_contents is None:
        return False
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(github_contents)
        print(f"Successfully updated {file_name}")
        return True
    except Exception as e:
        print(f"Error writing to file {file_name}: {e}")
        return False

def close_main_process():
    """Closes the running main.py process, whether it's running under py.exe or python.exe."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        cmdline = proc.info['cmdline']
        cwd = proc.info['cwd']
        # Check if the process is running the current main.py script
        if cmdline and (proc.info['name'] in ['py.exe', 'python.exe']) and MAIN_SCRIPT_PATH in cmdline and cwd == CURRENT_DIR:
            print(f"Attempting to close process: {proc.info['name']} (PID: {proc.info['pid']}) running {MAIN_SCRIPT_PATH}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                print(f"Process {proc.info['pid']} did not terminate, forcefully killing it.")
                proc.kill()
            ensure_process_terminated(proc.info['pid'])
            break

def ensure_process_terminated(pid):
    """Ensures that the process with the given PID is terminated."""
    try:
        proc = psutil.Process(pid)
        proc.wait(timeout=5)
    except psutil.TimeoutExpired:
        print(f"Process {pid} still running, forcefully killing it.")
        proc.kill()
    except psutil.NoSuchProcess:
        print(f"Process {pid} already terminated.")
    
    # Double-check that the process is truly terminated
    for _ in range(5):
        try:
            proc = psutil.Process(pid)
            proc.wait(timeout=1)
        except psutil.NoSuchProcess:
            print(f"Process {pid} is confirmed terminated.")
            return
        except psutil.TimeoutExpired:
            print(f"Waiting for process {pid} to terminate...")
        time.sleep(2)
    print(f"Process {pid} could not be terminated.")

def reopen_main():
    """Reopens main.py in a new command window."""
    try:
        print("Reopening main.py in a new command window...")
        subprocess.Popen(['cmd', '/c', 'start', 'python', MAIN_SCRIPT_PATH], shell=True)
    except Exception as e:
        print(f"Error reopening main.py: {e}")

def self_update():
    """Checks if the updater script itself needs to be updated and performs the update if necessary."""
    github_updater_contents = get_github_file_contents(GITHUB_RAW_URL + UPDATER_SCRIPT_NAME)
    if github_updater_contents is None:
        return False
    try:
        with open(UPDATER_SCRIPT_PATH, 'r', encoding='utf-8') as file:
            local_updater_contents = file.read()

        # If the contents differ, update the local updater.py
        if github_updater_contents != local_updater_contents:
            print("Updater script is outdated. Updating...")
            with open(UPDATER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
                file.write(github_updater_contents)
            print("Updater script updated. Restarting...")

            # Restart the script after the update
            subprocess.Popen(['cmd', '/c', 'start', 'python', UPDATER_SCRIPT_PATH], shell=True)
            sys.exit(0)  # Exit the current instance to allow the new one to take over
    
    except FileNotFoundError:
        # If updater.py does not exist locally, download it
        print(f"Updater script not found. Downloading...")
        with open(UPDATER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
            file.write(github_updater_contents)
        print("Updater script downloaded. Restarting...")

        # Restart the script after downloading
        subprocess.Popen(['cmd', '/c', 'start', 'python', UPDATER_SCRIPT_PATH], shell=True)
        sys.exit(0)  # Exit the current instance to allow the new one to take over
    
    except Exception as e:
        print(f"Error updating updater script: {e}")
        return False
