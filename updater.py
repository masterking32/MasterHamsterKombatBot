import os
import sys
import requests
import time

# Constants
LOCAL_FILE = "main.py"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/main.py"
RESTART_DELAY = 2  # Delay in seconds before restarting

def get_local_file_contents(file_path):
    with open(file_path, 'r') as file:
        contents = file.readlines()
    # Exclude the update logic section
    start_marker = "# BEGIN_UPDATE_LOGIC"
    end_marker = "# END_UPDATE_LOGIC"
    in_update_section = False
    filtered_contents = []
    for line in contents:
        if start_marker in line:
            in_update_section = True
        if not in_update_section:
            filtered_contents.append(line)
        if end_marker in line:
            in_update_section = False
    return "".join(filtered_contents)

def get_github_file_contents(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        response.raise_for_status()

def check_for_updates():
    try:
        local_contents = get_local_file_contents(LOCAL_FILE)
        github_contents = get_github_file_contents(GITHUB_RAW_URL)
        return local_contents != github_contents
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return False

def download_update():
    try:
        github_contents = get_github_file_contents(GITHUB_RAW_URL)
        with open(LOCAL_FILE, 'w') as file:
            file.write(github_contents)
        return True
    except Exception as e:
        print(f"Error downloading update: {e}")
        return False

def restart_program():
    try:
        print("Restarting program...")
        time.sleep(RESTART_DELAY)  # Optional delay before restarting
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        print(f"Error restarting program: {e}")

def update_check():
    if check_for_updates():
        print("New version available. Downloading update...")
        if download_update():
            print("Update downloaded. Restarting program...")
            restart_program()
        else:
            print("Failed to download update.")
    else:
        print("No updates available.")
