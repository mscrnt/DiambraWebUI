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
    """Call the TensorBoard start API when the app launches."""
    try:
        logger.info("Attempting to start TensorBoard via API...")
        response = requests.post("http://127.0.0.1:5000/tensorboard/start")
        if response.status_code == 200:
            logger.info("TensorBoard successfully started via API.")
        else:
            logger.error(f"Failed to start TensorBoard via API. Status code: {response.status_code}, Response: {response.text}")
    except requests.ConnectionError as e:
        logger.error(f"Connection error when trying to start TensorBoard: {e}")
    except Exception as e:
        logger.error(f"Unexpected error when trying to start TensorBoard: {e}")

Timer(1, start_tensorboard_via_api).start()
