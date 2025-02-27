# path: ./app.py

from flask import Flask, render_template, request, redirect, url_for
from app.global_state import training_manager, app_logger  # Import global instances
from app.routes.training_routes import create_training_blueprint
from app.routes.config_routes import create_config_blueprint
from app.routes.tensorboard_routes import create_tensorboard_blueprint
from app.routes.dashboard_routes import create_dashboard_blueprint
from app.routes.stream_routes import create_stream_blueprint
from app.routes.settings_routes import create_settings_blueprint
import logging
import requests
from threading import Timer
import subprocess
import os
import time
import psutil
import signal
import sys

def shutdown_server(signal_received, frame):
    """Handle graceful shutdown on Ctrl+C or system termination."""
    logger.info("[GLOBAL] Shutting down Flask server...")
    sys.exit(0)  # Exit cleanly without calling request.environ


# Register signal handlers for clean shutdown
signal.signal(signal.SIGINT, shutdown_server)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, shutdown_server)  # Handle system termination


# Try to get the FLASK_PORT from the environment
FLASK_PORT = os.getenv("FLASK_PORT")

# If FLASK_PORT is not set, try detecting Flask's actual running port
if not FLASK_PORT:
    def find_flask_port():
        """Find Flask's running port by checking processes."""
        for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                if process.info["name"] and "flask" in process.info["name"].lower():
                    cmdline = process.info["cmdline"]
                    if cmdline:
                        for index, arg in enumerate(cmdline):
                            if arg == "--port" and index + 1 < len(cmdline):
                                return cmdline[index + 1]  # Found the port
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return "5000"  # Default if nothing found

    FLASK_PORT = find_flask_port()

# Store FLASK_PORT in the environment for later use
os.environ["FLASK_PORT"] = FLASK_PORT

# Flask app initialization
app = Flask(__name__)
logger = app_logger  # Use the global logger

def is_docker_running():
    """Check if Docker is running."""
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Docker is installed but not running: {e.stderr.decode().strip()}")
        return False
    except FileNotFoundError:
        logger.error("Docker is not installed.")
        return False

@app.before_request
def suppress_logging():
    """Suppress logs for specific routes."""
    if request.path == "/training/render_status":
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

# Register Blueprints with logger explicitly passed
app.register_blueprint(create_training_blueprint(training_manager, app_logger), url_prefix="/training")
app.register_blueprint(create_config_blueprint(training_manager, app_logger), url_prefix="/config")
app.register_blueprint(create_tensorboard_blueprint(training_manager, app_logger), url_prefix="/tensorboard")
app.register_blueprint(create_stream_blueprint(training_manager, app_logger), url_prefix="/stream")
app.register_blueprint(create_dashboard_blueprint(training_manager, app_logger))
app.register_blueprint(create_settings_blueprint(app_logger), url_prefix="/settings")

@app.route("/", methods=["GET"])
def index():
    """
    Render the main index.html with training_dashboard.html as its default content.
    """
    if not is_docker_running():
        return redirect(url_for("docker_start"))
    return render_template(
        "index.html",
        title="Diambra Training Dashboard",
        year=2024,  # Example year
    )

@app.route("/docker/start", methods=["GET"])
def docker_start():
    """Attempt to start Docker and provide guidance."""
    if is_docker_running():
        return redirect(url_for("index"))  # Docker is already running

    try:
        if os.name == "nt":  # Windows
            docker_desktop_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
            if os.path.exists(docker_desktop_path):
                logger.info("Attempting to start Docker Desktop...")
                subprocess.Popen([docker_desktop_path], start_new_session=True)  # Run as a background process
                time.sleep(5)  # Allow time for Docker to start
                if is_docker_running():
                    logger.info("Docker Desktop started successfully.")
                    return redirect(url_for("index"))
                else:
                    logger.warning("Docker Desktop was started but is not running yet.")
            else:
                logger.error(f"Docker Desktop not found at {docker_desktop_path}.")
                return render_template(
                    "docker_start.html",
                    title="Docker Not Found",
                    message="Docker Desktop is not found in its default location. Please start it manually or check your installation.",
                )
        else:  # Linux or macOS
            result = subprocess.run(["sudo", "service", "docker", "start"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("Docker started successfully on Linux/macOS.")
            return redirect(url_for("index"))
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Docker: {e.stderr.decode().strip()}")
        return render_template(
            "docker_start.html",
            title="Docker Not Running",
            message="Docker is installed but not running. Please start Docker manually and refresh the page.",
        )
    except Exception as e:
        logger.error(f"Unexpected error while starting Docker: {str(e)}")
        return render_template(
            "docker_start.html",
            title="Error Starting Docker",
            message="An unexpected error occurred while trying to start Docker. Please start it manually and refresh the page.",
        )

def start_tensorboard_via_api():
    """Call the TensorBoard start API when the app launches, using the correct Flask port."""
    try:
        tensorboard_url = f"http://127.0.0.1:{FLASK_PORT}/tensorboard/start"
        logger.info(f"Attempting to start TensorBoard via API: {tensorboard_url}")
        response = requests.post(tensorboard_url)

        if response.status_code == 200:
            logger.info("TensorBoard successfully started via API.")
        else:
            logger.error(f"Failed to start TensorBoard via API. Status code: {response.status_code}, Response: {response.text}")
    except requests.ConnectionError as e:
        logger.error(f"Connection error when trying to start TensorBoard: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when trying to start TensorBoard: {e}")

Timer(1, start_tensorboard_via_api).start()
