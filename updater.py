import os
import sys
import requests
import time

# Constants
FILES = {
    "hamsterkombat.io-telegram-web-app.php": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/useful_files/hamsterkombat.io-telegram-web-app.php",
    "hamsterkombat.js": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/useful_files/hamsterkombat.js",
    "user-agents.md": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/useful_files/user-agents.md",
    ".gitignore": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/.gitignore",
    "README.MD": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/README.MD",
    "config.py.example": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/config.py.example",
    "main.py": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/main.py",
    "promogames.py": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/promogames.py",
    "requirements.txt": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/requirements.txt",
    "utilities.py": "https://raw.githubusercontent.com/masterking32/MasterHamsterKombatBot/main/utilities.py"
}
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
    updates_needed = []
    try:
        for local_file, github_url in FILES.items():
            local_contents = get_local_file_contents(local_file)
            github_contents = get_github_file_contents(github_url)
            if local_contents != github_contents:
                updates_needed.append(local_file)
    except Exception as e:
        print(f"Error checking for updates: {e}")
    return updates_needed

def download_update(file_name, github_url):
    try:
        github_contents = get_github_file_contents(github_url)
        with open(file_name, 'w') as file:
            file.write(github_contents)
        return True
    except Exception as e:
        print(f"Error downloading update for {file_name}: {e}")
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
    updates_needed = check_for_updates()
    if updates_needed:
        print("New versions available for:", ", ".join(updates_needed))
        all_updates_successful = True
        for file_name in updates_needed:
            github_url = FILES[file_name]
            if download_update(file_name, github_url):
                print(f"Update downloaded for {file_name}.")
            else:
                print(f"Failed to download update for {file_name}.")
                all_updates_successful = False
        if all_updates_successful:
            print("All updates downloaded. Restarting program...")
            restart_program()
        else:
            print("Some updates failed to download. Not restarting.")
    else:
        print("No updates available.")
