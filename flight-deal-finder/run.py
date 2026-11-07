"""Start the Flight Deal Finder:   python3 run.py   (Windows: py run.py)

The first run sets up a private Python environment in the .venv folder and
installs what's needed (takes a minute). After that it starts instantly.
"""
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
VENV_PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_environment():
    if sys.version_info < (3, 9):
        sys.exit("Python 3.9 or newer is needed. Download it from https://www.python.org/downloads/")
    if Path(sys.prefix).resolve() == VENV.resolve():
        return  # already running inside our environment
    marker = VENV / ".installed"
    if not marker.exists() or marker.read_text() != (HERE / "requirements.txt").read_text():
        print("First-time setup: installing what the app needs (about a minute)...")
        if not VENV_PY.exists():
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
        subprocess.check_call([str(VENV_PY), "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                               "-r", str(HERE / "requirements.txt")])
        marker.write_text((HERE / "requirements.txt").read_text())
    # Restart this script inside the environment
    sys.exit(subprocess.call([str(VENV_PY), str(HERE / "run.py"), *sys.argv[1:]]))


def ensure_env_file():
    env = HERE / ".env"
    if not env.exists():
        shutil.copy(HERE / ".env.example", env)
        print("Created a .env settings file. Put your SerpApi key in it (see README).")


def main():
    ensure_environment()
    ensure_env_file()
    sys.path.insert(0, str(HERE))
    from finder import alerts, config

    if "--check-alerts" in sys.argv:
        # For your computer's scheduler: check due price alerts once, then exit.
        for line in alerts.check_due() or ["No alerts due right now."]:
            print(line)
        return

    from finder.web import app

    url = f"http://localhost:{config.PORT}"
    print()
    print("  ✈️  Flight Deal Finder is running at", url)
    print("     ", "DEMO MODE (no API key yet — fake prices)" if config.demo_mode() else "Using your SerpApi key")
    print("      Keep this window open while you use it. Press Ctrl+C to stop.")
    print()
    import logging
    import flask.cli
    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # hide technical server messages
    flask.cli.show_server_banner = lambda *a, **k: None
    alerts.start_background_checker()
    if "--no-browser" not in sys.argv:
        threading.Thread(target=lambda: (time.sleep(1.2), webbrowser.open(url)), daemon=True).start()
    app.run(host="127.0.0.1", port=config.PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
