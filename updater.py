import os
import sys
import requests
import time
import psutil
import subprocess
import json
import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional

# Constants
GITHUB_REPO = "tboy1337/MasterHamsterKombatBot"  # Replace with your GitHub repo
GITHUB_BRANCH = "test"  # Replace with the branch you want to pull from
FILES_TO_CHECK_JSON = "files_to_check.json"  # JSON file in the repo that lists files to check
CHECK_DELAY = 60  # Delay in seconds between each update check cycle
MAX_RETRIES = 3  # Maximum number of retries for GitHub file fetching
RETRY_DELAY = 2  # Delay in seconds between retries

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory of the updater script
MAIN_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'main.py')  # Full path to main.py
UPDATER_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'updater.py')  # Full path to this updater script

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_sha256_hash(contents: str) -> str:
    """Calculate and return the SHA256 hash of the given string content."""
    return hashlib.sha256(contents.encode('utf-8')).hexdigest()

def get_github_file_contents(url: str) -> Optional[str]:
    """Fetch the contents of a file from GitHub with retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raises an error for bad responses
            response.encoding = 'utf-8'  # Ensure the response is handled as UTF-8
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching file from GitHub: {url} - Attempt {attempt}/{MAX_RETRIES} - {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
    return None

def get_local_file_contents(file_path: str) -> Optional[str]:
    """Read and return the contents of a local file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"File {file_path} not found. It will be downloaded.")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"Error reading local file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"General error reading local file {file_path}: {e}")
        return None

def check_for_updates(files_to_check: Dict[str, str]) -> List[Tuple[str, str]]:
    """Check if any files need to be updated by comparing local and GitHub SHA256 hashes."""
    updates_needed = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_file = {executor.submit(get_github_file_contents, github_path): (local_file, github_path) 
                          for local_file, github_path in files_to_check.items()}
        for future in future_to_file:
            local_file, github_path = future_to_file[future]
            try:
                github_contents = future.result()
                local_contents = get_local_file_contents(local_file)
                if github_contents is None or local_contents is None:
                    updates_needed.append((local_file, github_path))
                    logger.info(f"Update needed for {local_file} due to missing or corrupt content.")
                elif get_sha256_hash(local_contents) != get_sha256_hash(github_contents):
                    updates_needed.append((local_file, github_path))
                    logger.info(f"Update needed for {local_file} due to hash mismatch.")
                else:
                    logger.info(f"No update needed for {local_file}")
            except Exception as e:
                logger.error(f"Error processing file {local_file}: {e}")
    return updates_needed

def get_files_to_check() -> Dict[str, str]:
    """Fetch the list of files to check for updates from a JSON file in the GitHub repository."""
    files = {}
    json_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{FILES_TO_CHECK_JSON}"
    json_content = get_github_file_contents(json_url)
    if json_content:
        try:
            files_dict = json.loads(json_content)
            for local_path, repo_path in files_dict.items():
                github_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{repo_path}"
                files[local_path] = github_url
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
    return files

def download_update(file_name: str, github_url: str) -> bool:
    """Download and save the updated file from GitHub atomically."""
    github_contents = get_github_file_contents(github_url)
    if github_contents is None:
        return False
    try:
        os.makedirs(os.path.dirname(file_name), exist_ok=True)  # Ensure the directory exists
        temp_file_name = f"{file_name}.tmp"
        with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
            temp_file.write(github_contents)
        os.replace(temp_file_name, file_name)  # Atomic replace of the original file
        logger.info(f"Successfully updated {file_name}")
        return True
    except UnicodeEncodeError as e:
        logger.error(f"Error writing to file {file_name} with UTF-8 encoding: {e}")
        return False
    except Exception as e:
        logger.error(f"General error writing to file {file_name}: {e}")
        return False

def close_main_process():
    """Attempt to close the main.py process if it's running."""
    process_found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        cmdline = proc.info['cmdline']
        cwd = proc.info['cwd']
        if cmdline and (proc.info['name'] in ['py.exe', 'python.exe']) and MAIN_SCRIPT_PATH in cmdline and cwd == CURRENT_DIR:
            process_found = True
            logger.info(f"Attempting to close process: {proc.info['name']} (PID: {proc.info['pid']}) running {MAIN_SCRIPT_PATH}")
            proc.terminate()  # Attempt to gracefully terminate the process
            try:
                proc.wait(timeout=5)  # Wait for up to 5 seconds for the process to terminate
            except psutil.TimeoutExpired:
                logger.warning(f"Process {proc.info['pid']} did not terminate, forcefully killing it.")
                proc.kill()  # Forcefully terminate the process if it doesn't close
            finally:
                ensure_process_terminated(proc.info['pid'])  # Ensure the process is terminated
            break

    if not process_found:
        logger.info(f"No running process found for {MAIN_SCRIPT_PATH}.")

def ensure_process_terminated(pid: int):
    """Ensures that the process with the given PID is terminated."""
    try:
        proc = psutil.Process(pid)
        proc.wait(timeout=5)
    except psutil.TimeoutExpired:
        logger.warning(f"Process {pid} still running, forcefully killing it.")
        proc.kill()
    except psutil.NoSuchProcess:
        logger.info(f"Process {pid} already terminated.")

    for _ in range(5):  # Retry up to 5 times with a short delay between
        try:
            proc = psutil.Process(pid)
            proc.wait(timeout=1)
        except psutil.NoSuchProcess:
            logger.info(f"Process {pid} is confirmed terminated.")
            return
        except psutil.TimeoutExpired:
            logger.warning(f"Waiting for process {pid} to terminate...")
        time.sleep(2)
    logger.error(f"Process {pid} could not be terminated.")

def reopen_main():
    """Reopen the main.py script in a new command window."""
    try:
        logger.info("Reopening main.py in a new command window...")
        subprocess.Popen(['cmd', '/c', 'start', 'python', MAIN_SCRIPT_PATH], shell=True)
    except Exception as e:
        logger.error(f"Error reopening main.py: {e}")

def self_update_check():
    """Check if the updater script itself needs updating and update if necessary."""
    github_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/updater.py"
    github_contents = get_github_file_contents(github_url)
    local_contents = get_local_file_contents(UPDATER_SCRIPT_PATH)
    if github_contents and local_contents and get_sha256_hash(local_contents) != get_sha256_hash(github_contents):
        logger.info("Updater script needs updating.")
        try:
            os.makedirs(os.path.dirname(UPDATER_SCRIPT_PATH), exist_ok=True)  # Ensure directory exists
            temp_file_name = f"{UPDATER_SCRIPT_PATH}.tmp"
            with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
                temp_file.write(github_contents)
            os.replace(temp_file_name, UPDATER_SCRIPT_PATH)  # Atomic replace of the original file
            logger.info("Updater script updated. Restarting...")
            subprocess.Popen([sys.executable, UPDATER_SCRIPT_PATH])
            sys.exit(0)  # Exit the current script, letting the new one take over
        except UnicodeEncodeError as e:
            logger.error(f"Error updating the updater script with UTF-8 encoding: {e}")
        except Exception as e:
            logger.error(f"General error updating the updater script: {e}")

def update_check():
    """Check for updates to the main script and any other files."""
    files_to_check = get_files_to_check()
    updates_needed = check_for_updates(files_to_check)
    if updates_needed:
        close_main_process()  # Attempt to close main.py process if it's running
        all_updates_successful = True
        for file_name, github_path in updates_needed:
            if not download_update(file_name, github_path):
                all_updates_successful = False
        if all_updates_successful:
            logger.info("All updates downloaded.")
            time.sleep(2)  # Add a delay to ensure old process has completely terminated
            reopen_main()  # Always reopen main.py after updates
        else:
            logger.error("Some updates failed to download.")
    else:
        logger.info("No updates available.")

def main_loop():
    """Main loop that continuously checks for updates."""
    while True:
        self_update_check()  # Check for updates to the updater script
        update_check()  # Check for updates to the other files
        logger.info(f"Waiting {CHECK_DELAY} seconds before next check...")
        time.sleep(CHECK_DELAY)  # Wait before checking again

if __name__ == "__main__":
    main_loop()
