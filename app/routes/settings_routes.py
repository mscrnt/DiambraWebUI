# path: app/routes/settings_routes.py

from flask import Blueprint, request, jsonify, render_template
import os
from app import DEFAULT_PATHS

def create_settings_blueprint(app_logger):
    """
    Create the settings blueprint to handle Diambra.ai token integration.
    :return: Settings blueprint.
    """
    logger = app_logger.__class__("settings_routes") 

    settings_blueprint = Blueprint("settings_routes", __name__)

    credentials_file_path = os.path.join(os.path.dirname(__file__), "../dimabra/credentials")
    credentials_file_path = os.path.abspath(credentials_file_path)   

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
            return jsonify({"error": "Token is required"}), 400

        try:
            # Ensure the directory exists
            credentials_dir = DEFAULT_PATHS["dimabra_path"]
            os.makedirs(credentials_dir, exist_ok=True)

            # Save the token to the credentials file
            credentials_file = os.path.join(credentials_dir, "credentials")
            with open(credentials_file, "w") as cred_file:
                cred_file.write(f"{token}")

            logger.info(f"Token saved successfully to {credentials_file}")
            return jsonify({"success": True, "message": "Token saved successfully!"}), 200
        except Exception as e:
            logger.error(f"Error saving token: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @settings_blueprint.route("/check-credentials", methods=["GET"])
    def check_credentials():
        """
        Check if the credentials file exists.
        """
        logger.info("Checking if credentials file exists.")
        logger.debug(f"Looking for credentials file at: {credentials_file_path}")
        if os.path.exists(credentials_file_path):
            logger.info("Credentials file exists.")
            return jsonify({"exists": True})
        logger.warning("Credentials file does not exist.")
        return jsonify({"exists": False})

    return settings_blueprint
