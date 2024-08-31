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
import traceback
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='updater.log', filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)
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
    logger.debug("Loading configuration...")
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
logger.info(f"Configuration loaded: {config}")

# ... [All other existing classes and functions remain unchanged] ...

class ProcessManager:
    @staticmethod
    def close_main_process():
        logger.debug("Attempting to close main process...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
            try:
                cmdline = proc.cmdline()
                if 'python' in cmdline[0].lower() and config.MAIN_SCRIPT_PATH in cmdline:
                    logger.info(f"Attempting to close process: {proc.name()} (PID: {proc.pid}) running {config.MAIN_SCRIPT_PATH}")
                    ProcessManager._terminate_process(proc)
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        logger.info("No main process found to close.")
        return False

    @staticmethod
    def _terminate_process(proc):
        try:
            logger.debug(f"Terminating process: {proc.pid}")
            proc.terminate()
            proc.wait(timeout=10)
        except psutil.TimeoutExpired:
            logger.warning(f"Process {proc.pid} did not terminate, forcefully killing it.")
            proc.kill()
        finally:
            ProcessManager._ensure_process_terminated(proc.pid)

    @staticmethod
    def _ensure_process_terminated(pid):
        try:
            proc = psutil.Process(pid)
            proc.wait(timeout=5)
        except psutil.NoSuchProcess:
            logger.info(f"Process {pid} is confirmed terminated.")
        except psutil.TimeoutExpired:
            logger.error(f"Process {pid} could not be terminated.")

    @staticmethod
    def reopen_main():
        try:
            logger.info("Reopening main.py in a new visible terminal window...")
            subprocess.Popen(['start', 'cmd', '/k', sys.executable, config.MAIN_SCRIPT_PATH], shell=True)
        except Exception as e:
            logger.error(f"Error reopening main.py: {e}")

# ... [All other existing code remains unchanged] ...

if __name__ == "__main__":
    try:
        logger.info("Starting updater script...")
        os.system('color')  # This is a no-op that keeps the window open on Windows
        asyncio.run(main_loop())
    except Exception as e:
        logger.critical(f"Fatal error in updater script: {e}")
        logger.critical(traceback.format_exc())
    finally:
        input("Press Enter to exit...")  # Keep the window open
