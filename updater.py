import os
import sys
import time
import requests
import json
##############
# Constants
GITHUB_RAW_URL = "https://raw.githubusercontent.com/tboy1337/MasterHamsterKombatBot/test/"
FILES_CONFIG_URL = GITHUB_RAW_URL + "files_to_update.json"
CHECK_DELAY = 60  # Delay in seconds between each update check cycle
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory of the updater script
UPDATER_SCRIPT_NAME = "updater.py"
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

def update_check():
    """Checks for updates to the files listed in the configuration file."""
    file_list = fetch_file_list()
    updates_needed = []
    restart_required = False

    for file_info in file_list:
        file_name = file_info.get("name")
        github_url = GITHUB_RAW_URL + file_name
        local_contents = get_local_file_contents(file_name)
        github_contents = get_github_file_contents(github_url)

        if local_contents is None or local_contents != github_contents:
            updates_needed.append(file_name)

    if updates_needed:
        for file_name in updates_needed:
            github_url = GITHUB_RAW_URL + file_name
            if update_file(file_name, github_url):
                if file_name == UPDATER_SCRIPT_NAME:
                    restart_required = True

    return restart_required

def main_loop():
    """Main loop to continuously check for updates and apply them."""
    while True:
        if update_check():
            print("Updater script was updated. Restarting required.")
            sys.exit(100)  # Signal that a restart is required
        print(f"Sleeping for {CHECK_DELAY} seconds before next check...")
        time.sleep(CHECK_DELAY)

if __name__ == "__main__":
    main_loop()
