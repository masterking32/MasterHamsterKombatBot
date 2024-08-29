import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

UPDATER_SCRIPT_PATH = 'updater.py'

class UpdaterHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(UPDATER_SCRIPT_PATH):
            print(f"{UPDATER_SCRIPT_PATH} has been modified. Restarting...")
            restart_updater()

def restart_updater():
    subprocess.Popen([sys.executable, UPDATER_SCRIPT_PATH])

def monitor_updater():
    event_handler = UpdaterHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    monitor_updater()
