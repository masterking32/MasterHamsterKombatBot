import os
import sys
import requests
import time
import psutil
import subprocess
import json
#
# Constants
GITHUB_RAW_URL = "https://raw.githubusercontent.com/tboy1337/MasterHamsterKombatBot/test/"
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
        print("Failed to fetch updater script from GitHub.")
        return False
    try:
        # Read the local updater.py file
        with open(UPDATER_SCRIPT_PATH, 'r', encoding='utf-8') as file:
            local_updater_contents = file.read()

        # If the contents differ, update the local updater.py
        if github_updater_contents != local_updater_contents:
            print("Updater script is outdated. Updating...")
            with open(UPDATER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
                file.write(github_updater_contents)
            print("Updater script updated. Restarting...")

            # Ensure file is flushed and delay before restart
            file.flush()
            os.fsync(file.fileno())
            time.sleep(1)  # Short delay to ensure everything is written

            # Restart the script after the update
            print("Executing os.execl to restart script...")
            os.execl(sys.executable, sys.executable, UPDATER_SCRIPT_PATH)  # Directly replace the current process
    
    except FileNotFoundError:
        # If the file was removed or can't be found after starting, handle it gracefully
        print(f"Updater script not found. Attempting to restore...")

        # Attempt to restore the updater script
        with open(UPDATER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
            file.write(github_updater_contents)
        print("Updater script restored. Restarting...")

        # Ensure file is flushed and delay before restart
        file.flush()
        os.fsync(file.fileno())
        time.sleep(1)  # Short delay to ensure everything is written

        # Restart the script after restoring
        print("Executing os.execl to restart script...")
        os.execl(sys.executable, sys.executable, UPDATER_SCRIPT_PATH)  # Directly replace the current process
    
    except Exception as e:
        print(f"Error updating updater script: {e}")
        return False

def update_check():
    """Checks for updates to the updater script itself and other files, updates them if necessary, and restarts main.py."""
    self_update()  # First, ensure the updater itself is up-to-date
    file_list = fetch_file_list()  # Fetch the dynamic list of files to update
    updates_needed = []

    for file_info in file_list:
        file_name = file_info.get("name")
        github_url = GITHUB_RAW_URL + file_name
        local_contents = get_local_file_contents(file_name)
        github_contents = get_github_file_contents(github_url)

        # Add to updates if the file is missing or outdated
        if local_contents is None or local_contents != github_contents:
            updates_needed.append(file_name)

    if updates_needed:
        close_main_process()  # Close main.py if updates are needed
        all_updates_successful = True
        for file_name in updates_needed:
            github_url = GITHUB_RAW_URL + file_name
            if not update_file(file_name, github_url):
                all_updates_successful = False
        if all_updates_successful:
            print("All updates downloaded.")
            reopen_main()  # Reopen main.py after updates
        else:
            print("Some updates failed to download.")
    else:
        print("No updates available.")

def main_loop():
    """Continuously checks for updates and applies them."""
    while True:
        update_check()
        time.sleep(CHECK_DELAY)

if __name__ == "__main__":
    main_loop()
