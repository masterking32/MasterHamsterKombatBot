import os
import sys
import requests
import time
import psutil
import subprocess
import json

# Constants
GITHUB_REPO = "tboy1337/MasterHamsterKombatBot"  # Replace with your GitHub repo
GITHUB_BRANCH = "test"  # Replace with the branch you want to pull from
FILES_TO_CHECK_JSON = "files_to_check.json"  # JSON file in the repo that lists files to check
CHECK_DELAY = 60  # Delay in seconds between each update check cycle
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory of the updater script
MAIN_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'main.py')  # Full path to main.py
UPDATER_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'updater.py')  # Full path to this updater script

def get_github_file_contents(url):
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

def check_for_updates(files_to_check):
    updates_needed = []
    for local_file, github_path in files_to_check.items():
        local_contents = get_local_file_contents(local_file)
        github_contents = get_github_file_contents(github_path)
        if local_contents is None:  # If the file is missing or an error occurred, download it
            updates_needed.append((local_file, github_path))
            continue
        if github_contents is None:
            continue  # Skip this file if there's an error fetching it from GitHub
        if local_contents != github_contents:
            updates_needed.append((local_file, github_path))
            print(f"Update needed for {local_file}")
        else:
            print(f"No update needed for {local_file}")
    return updates_needed

def get_files_to_check():
    files = {}
    # Construct the URL to the JSON file in the repo
    json_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{FILES_TO_CHECK_JSON}"
    json_content = get_github_file_contents(json_url)
    if json_content:
        try:
            files_dict = json.loads(json_content)
            for local_path, repo_path in files_dict.items():
                # Construct the URL for each file based on the file path in the repo
                github_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{repo_path}"
                files[local_path] = github_url
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
    return files

def download_update(file_name, github_url):
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

def update_check():
    files_to_check = get_files_to_check()
    updates_needed = check_for_updates(files_to_check)
    if updates_needed:
        close_main_process()  # Attempt to close main.py process if it's running
        all_updates_successful = True
        for file_name, github_path in updates_needed:
            if not download_update(file_name, github_path):
                all_updates_successful = False
        if all_updates_successful:
            print("All updates downloaded.")
            time.sleep(2)  # Add a delay to ensure old process has completely terminated
            reopen_main()  # Always reopen main.py after updates
        else:
            print("Some updates failed to download.")
    else:
        print("No updates available.")

def self_update_check():
    # Check for updates to the updater script itself
    github_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/updater.py"
    github_contents = get_github_file_contents(github_url)
    local_contents = get_local_file_contents(UPDATER_SCRIPT_PATH)
    if github_contents and local_contents != github_contents:
        print("Updater script needs updating.")
        with open(UPDATER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
            file.write(github_contents)
        print("Updater script updated. Restarting...")
        subprocess.Popen([sys.executable, UPDATER_SCRIPT_PATH])
        sys.exit(0)  # Exit the current script, letting the new one take over

def get_local_file_contents(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            contents = file.read()
        return contents
    except FileNotFoundError:
        print(f"File {file_path} not found. It will be downloaded.")
        return None
    except UnicodeDecodeError as e:
        print(f"Error reading local file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"General error reading local file {file_path}: {e}")
        return None

def close_main_process():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        cmdline = proc.info['cmdline']
        cwd = proc.info['cwd']
        if cmdline and (proc.info['name'] in ['py.exe', 'python.exe']) and MAIN_SCRIPT_PATH in cmdline and cwd == CURRENT_DIR:
            print(f"Attempting to close process: {proc.info['name']} (PID: {proc.info['pid']}) running {MAIN_SCRIPT_PATH}")
            proc.terminate()  # Attempt to gracefully terminate the process
            try:
                proc.wait(timeout=5)  # Wait for up to 5 seconds for the process to terminate
            except psutil.TimeoutExpired:
                print(f"Process {proc.info['pid']} did not terminate, forcefully killing it.")
                proc.kill()  # Forcefully terminate the process if it doesn't close
            finally:
                ensure_process_terminated(proc.info['pid'])  # Ensure the process is terminated
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

def reopen_main():
    try:
        print("Reopening main.py in a new command window...")
        subprocess.Popen(['cmd', '/c', 'start', 'python', MAIN_SCRIPT_PATH], shell=True)
    except Exception as e:
        print(f"Error reopening main.py: {e}")

def main_loop():
    while True:
        self_update_check()  # Check for updates to the updater script
        update_check()  # Check for updates to the other files
        print(f"Waiting {CHECK_DELAY} seconds before next check...")
        time.sleep(CHECK_DELAY)  # Wait before checking again

if __name__ == "__main__":
    main_loop()
