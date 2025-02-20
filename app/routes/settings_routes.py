# path: app/routes/settings_routes.py

from flask import Blueprint, request, render_template
import os
import subprocess
from app import DEFAULT_PATHS

def create_settings_blueprint(app_logger):
    """
    Create the settings blueprint to handle Diambra.ai token integration and settings operations.
    :return: Settings blueprint.
    """
    logger = app_logger.__class__("settings_routes")

    settings_blueprint = Blueprint("settings_routes", __name__)

    credentials_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../dimabra/credentials"))
    checkpoints_dir = os.path.abspath(os.path.join(os.getcwd(), "checkpoints"))
    logs_dir = os.path.abspath(os.path.join(os.getcwd(), "logs"))

    @settings_blueprint.route("/", methods=["GET"])
    def settings_page():
        """
        Render the settings page.
        """
        logger.info("Rendering settings page")
        return render_template("settings.html", title="Settings")

    @settings_blueprint.route("/save-token", methods=["POST"])
    def save_token():
        """
        Save the Diambra.ai token to a credentials file.
        """
        logger.info("Saving token to credentials file")
        token = request.form.get("token")
        if not token:
            return {"error": "Token is required"}, 400

        try:
            # Ensure the directory exists
            credentials_dir = DEFAULT_PATHS["dimabra_path"]
            os.makedirs(credentials_dir, exist_ok=True)

            # Save the token to the credentials file
            credentials_file = os.path.join(credentials_dir, "credentials")
            with open(credentials_file, "w") as cred_file:
                cred_file.write(f"{token}")

            logger.info(f"Token saved successfully to {credentials_file}")
            return {"success": True, "message": "Token saved successfully!"}, 200
        except Exception as e:
            logger.error(f"Error saving token: {str(e)}")
            return {"error": str(e)}, 500

    @settings_blueprint.route("/check-credentials", methods=["GET"])
    def check_credentials():
        """
        Check if the credentials file exists.
        """
        logger.info("Checking if credentials file exists.")
        logger.debug(f"Looking for credentials file at: {credentials_file_path}")
        if os.path.exists(credentials_file_path):
            logger.info("Credentials file exists.")
            return {"exists": True}
        logger.warning("Credentials file does not exist.")
        return {"exists": False}

    def open_folder(path):
        """
        Opens a folder in the file explorer and ensures it only executes once per request.
        """
        try:
            if os.name == "nt":  # Windows
                subprocess.Popen(f'explorer "{path}"', shell=True)  # Uses Popen to prevent blocking
            elif os.name == "posix":  # macOS and Linux
                subprocess.run(["xdg-open", path], check=False)
            logger.info(f"Opened folder: {path}")
            return "", 204  # No content response
        except Exception as e:
            logger.error(f"Error opening folder {path}: {str(e)}")
            return "", 500  # No message, just status code

    @settings_blueprint.route("/open-checkpoints", methods=["GET"])
    def open_checkpoints():
        """
        Open the checkpoints directory.
        """
        return open_folder(checkpoints_dir)

    @settings_blueprint.route("/open-logs", methods=["GET"])
    def open_logs():
        """
        Open the logs directory.
        """
        return open_folder(logs_dir)

    return settings_blueprint
