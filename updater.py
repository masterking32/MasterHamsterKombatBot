import os
import sys
import requests
import time
import psutil
import subprocess
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
GITHUB_REPO = "tboy1337/MasterHamsterKombatBot"
GITHUB_BRANCH = "test"
FILES_TO_CHECK_JSON = "files_to_check.json"
CHECK_DELAY = 60
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'main.py')
UPDATER_SCRIPT_PATH = os.path.join(CURRENT_DIR, 'updater.py')
MAX_RETRIES = 3
RETRY_DELAY = 5

class UpdaterError(Exception):
    """Custom exception for updater-related errors."""
    pass

def get_github_file_contents(url: str) -> str:
    """Fetch the contents of a file from GitHub with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed: Error fetching file from GitHub: {url} - {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise UpdaterError(f"Failed to fetch file from GitHub after {MAX_RETRIES} attempts: {url}") from e

def get_local_file_contents(file_path: str) -> str:
    """Read and return the contents of a local file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(f"File {file_path} not found. It will be downloaded.")
        return None
    except Exception as e:
        raise UpdaterError(f"Error reading local file {file_path}: {e}")

def calculate_file_hash(content: str) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def check_for_updates(files_to_check: Dict[str, str]) -> List[Tuple[str, str]]:
    """Check if any files need to be updated by comparing hashes."""
    updates_needed = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_file = {executor.submit(get_github_file_contents, github_path): (local_file, github_path) 
                          for local_file, github_path in files_to_check.items()}
        for future in future_to_file:
            local_file, github_path = future_to_file[future]
            try:
                github_contents = future.result()
                local_contents = get_local_file_contents(local_file)
                if local_contents is None or calculate_file_hash(local_contents) != calculate_file_hash(github_contents):
                    updates_needed.append((local_file, github_path))
                    logger.info(f"Update needed for {local_file}")
                else:
                    logger.info(f"No update needed for {local_file}")
            except UpdaterError as e:
                logger.error(f"Error processing file {local_file}: {e}")
    return updates_needed

def get_files_to_check() -> Dict[str, str]:
    """Fetch the list of files to check for updates from a JSON file in the GitHub repository."""
    json_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{FILES_TO_CHECK_JSON}"
    json_content = get_github_file_contents(json_url)
    try:
        files_dict = json.loads(json_content)
        return {local_path: f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{repo_path}"
                for local_path, repo_path in files_dict.items()}
    except json.JSONDecodeError as e:
        raise UpdaterError(f"Error decoding JSON: {e}")

def download_update(file_name: str, github_url: str) -> bool:
    """Download and save the updated file from GitHub."""
    github_contents = get_github_file_contents(github_url)
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(github_contents)
        logger.info(f"Successfully updated {file_name}")
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_name}: {e}")
        return False

def close_main_process() -> None:
    """Attempt to close the main.py process if it's running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        if proc.info['name'] in ['py.exe', 'python.exe'] and MAIN_SCRIPT_PATH in proc.info.get('cmdline', []) and proc.info['cwd'] == CURRENT_DIR:
            logger.info(f"Attempting to close process: {proc.info['name']} (PID: {proc.info['pid']}) running {MAIN_SCRIPT_PATH}")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                logger.warning(f"Process {proc.info['pid']} did not terminate, forcefully killing it.")
                proc.kill()
            finally:
                ensure_process_terminated(proc.info['pid'])
            return
    logger.info(f"No running process found for {MAIN_SCRIPT_PATH}.")

def ensure_process_terminated(pid: int) -> None:
    """Ensures that the process with the given PID is terminated."""
    for _ in range(5):
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

def reopen_main() -> None:
    """Reopen the main.py script in a new command window."""
    try:
        logger.info("Reopening main.py in a new command window...")
        subprocess.Popen(['cmd', '/c', 'start', 'python', MAIN_SCRIPT_PATH], shell=True)
    except Exception as e:
        logger.error(f"Error reopening main.py: {e}")

def self_update_check() -> None:
    """Check if the updater script itself needs updating and update if necessary."""
    github_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/updater.py"
    github_contents = get_github_file_contents(github_url)
    local_contents = get_local_file_contents(UPDATER_SCRIPT_PATH)
    if calculate_file_hash(local_contents) != calculate_file_hash(github_contents):
        logger.info("Updater script needs updating.")
        try:
            with open(UPDATER_SCRIPT_PATH, 'w', encoding='utf-8') as file:
                file.write(github_contents)
            logger.info("Updater script updated. Restarting...")
            subprocess.Popen([sys.executable, UPDATER_SCRIPT_PATH])
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error updating the updater script: {e}")

def update_check() -> None:
    """Check for updates to the main script and any other files."""
    try:
        files_to_check = get_files_to_check()
        updates_needed = check_for_updates(files_to_check)
        if updates_needed:
            close_main_process()
            all_updates_successful = all(download_update(file_name, github_path) for file_name, github_path in updates_needed)
            if all_updates_successful:
                logger.info("All updates downloaded.")
                time.sleep(2)
                reopen_main()
            else:
                logger.error("Some updates failed to download.")
        else:
            logger.info("No updates available.")
    except UpdaterError as e:
        logger.error(f"Update check failed: {e}")

def main_loop() -> None:
    """Main loop that continuously checks for updates."""
    while True:
        try:
            self_update_check()
            update_check()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            logger.info(f"Waiting {CHECK_DELAY} seconds before next check...")
            time.sleep(CHECK_DELAY)

if __name__ == "__main__":
    main_loop()
