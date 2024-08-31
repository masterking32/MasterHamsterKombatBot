import os
import sys
import time
import psutil
import subprocess
import json
import logging
import asyncio
import aiohttp
import tempfile
import shutil
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Config:
    GITHUB_REPO: str
    GITHUB_BRANCH: str
    FILES_TO_CHECK_JSON: str
    CHECK_DELAY: int
    CURRENT_DIR: str
    MAIN_SCRIPT_PATH: str
    UPDATER_SCRIPT_PATH: str

def load_config() -> Config:
    return Config(
        GITHUB_REPO="tboy1337/MasterHamsterKombatBot",
        GITHUB_BRANCH="test",
        FILES_TO_CHECK_JSON="files_to_check.json",
        CHECK_DELAY=60,
        CURRENT_DIR=os.path.dirname(os.path.abspath(__file__)),
        MAIN_SCRIPT_PATH=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py'),
        UPDATER_SCRIPT_PATH=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'updater.py')
    )

config = load_config()

class GitHubAPI:
    @staticmethod
    async def get_file_contents(session: aiohttp.ClientSession, url: str) -> Optional[str]:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text(encoding='utf-8')
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching file from GitHub: {e}")
            return None

class FileManager:
    @staticmethod
    def get_local_file_contents(file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.info(f"File {file_path} not found. It will be downloaded.")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading local file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading local file {file_path}: {e}")
            return None

    @staticmethod
    def write_file(file_name: str, contents: str) -> bool:
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(contents)
            logger.info(f"Successfully updated {file_name}")
            return True
        except UnicodeEncodeError as e:
            logger.error(f"Encoding error writing to file {file_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing to file {file_name}: {e}")
            return False

class ProcessManager:
    @staticmethod
    def close_main_process():
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
            cmdline = proc.info['cmdline']
            cwd = proc.info['cwd']
            if cmdline and (proc.info['name'] in ['py.exe', 'python.exe']) and config.MAIN_SCRIPT_PATH in cmdline and cwd == config.CURRENT_DIR:
                logger.info(f"Attempting to close process: {proc.info['name']} (PID: {proc.info['pid']}) running {config.MAIN_SCRIPT_PATH}")
                ProcessManager._terminate_process(proc)
                break

    @staticmethod
    def _terminate_process(proc):
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except psutil.TimeoutExpired:
            logger.warning(f"Process {proc.info['pid']} did not terminate, forcefully killing it.")
            proc.kill()
        finally:
            ProcessManager._ensure_process_terminated(proc.info['pid'])

    @staticmethod
    def _ensure_process_terminated(pid):
        for _ in range(5):
            try:
                proc = psutil.Process(pid)
                proc.wait(timeout=1)
            except psutil.NoSuchProcess:
                logger.info(f"Process {pid} is confirmed terminated.")
                return
            except psutil.TimeoutExpired:
                logger.info(f"Waiting for process {pid} to terminate...")
            time.sleep(2)
        logger.error(f"Process {pid} could not be terminated.")

    @staticmethod
    def reopen_main():
        try:
            logger.info("Reopening main.py in a new command window...")
            subprocess.Popen(['cmd', '/c', 'start', 'python', config.MAIN_SCRIPT_PATH], shell=True)
        except Exception as e:
            logger.error(f"Error reopening main.py: {e}")

class Updater:
    def __init__(self):
        self.github_api = GitHubAPI()
        self.file_manager = FileManager()

    async def get_files_to_check(self, session: aiohttp.ClientSession) -> Dict[str, str]:
        files = {}
        json_url = f"https://raw.githubusercontent.com/{config.GITHUB_REPO}/{config.GITHUB_BRANCH}/{config.FILES_TO_CHECK_JSON}"
        json_content = await self.github_api.get_file_contents(session, json_url)
        if json_content:
            try:
                files_dict = json.loads(json_content)
                for local_path, repo_path in files_dict.items():
                    github_url = f"https://raw.githubusercontent.com/{config.GITHUB_REPO}/{config.GITHUB_BRANCH}/{repo_path}"
                    files[local_path] = github_url
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
        return files

    async def check_for_updates(self, session: aiohttp.ClientSession, files_to_check: Dict[str, str]) -> List[Tuple[str, str]]:
        updates_needed = []
        for local_file, github_path in files_to_check.items():
            local_contents = self.file_manager.get_local_file_contents(local_file)
            github_contents = await self.github_api.get_file_contents(session, github_path)
            if local_contents is None or (github_contents and local_contents != github_contents):
                updates_needed.append((local_file, github_path))
                logger.info(f"Update needed for {local_file}")
            else:
                logger.info(f"No update needed for {local_file}")
        return updates_needed

    async def download_update(self, session: aiohttp.ClientSession, file_name: str, github_url: str) -> bool:
        github_contents = await self.github_api.get_file_contents(session, github_url)
        if github_contents is None:
            return False
        
        try:
            # Create a temporary file using utf-8 encoding
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(github_contents)
                temp_file_path = temp_file.name

            # Move the temporary file to the final location
            shutil.move(temp_file_path, file_name)
            logger.info(f"Successfully updated {file_name}")
            return True
        except UnicodeEncodeError as e:
            logger.error(f"Encoding error while writing update for {file_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating file {file_name}: {e}")
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            return False

    async def update_check(self):
        async with aiohttp.ClientSession() as session:
            files_to_check = await self.get_files_to_check(session)
            updates_needed = await self.check_for_updates(session, files_to_check)
            if updates_needed:
                ProcessManager.close_main_process()
                update_tasks = [self.download_update(session, file_name, github_path) for file_name, github_path in updates_needed]
                update_results = await asyncio.gather(*update_tasks)
                if all(update_results):
                    logger.info("All updates downloaded.")
                    await asyncio.sleep(2)
                    ProcessManager.reopen_main()
                else:
                    logger.error("Some updates failed to download.")
            else:
                logger.info("No updates available.")

    async def self_update_check(self):
        async with aiohttp.ClientSession() as session:
            github_url = f"https://raw.githubusercontent.com/{config.GITHUB_REPO}/{config.GITHUB_BRANCH}/updater.py"
            github_contents = await self.github_api.get_file_contents(session, github_url)
            local_contents = self.file_manager.get_local_file_contents(config.UPDATER_SCRIPT_PATH)
            if github_contents and local_contents != github_contents:
                logger.info("Updater script needs updating.")
                if await self.download_update(session, config.UPDATER_SCRIPT_PATH, github_url):
                    logger.info("Updater script updated. Restarting...")
                    subprocess.Popen([sys.executable, config.UPDATER_SCRIPT_PATH])
                    sys.exit(0)

async def main_loop():
    updater = Updater()
    while True:
        await updater.self_update_check()
        await updater.update_check()
        logger.info(f"Waiting {config.CHECK_DELAY} seconds before next check...")
        await asyncio.sleep(config.CHECK_DELAY)

if __name__ == "__main__":
    asyncio.run(main_loop())
