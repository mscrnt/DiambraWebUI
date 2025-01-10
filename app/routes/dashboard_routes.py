# path: routes/dashboard_routes.py

from flask import Blueprint, render_template, jsonify, request
from app import (
    DEFAULT_HYPERPARAMETERS,
    DEFAULT_TRAINING_CONFIG,
    DEFAULT_PATHS,
    ENV_SETTINGS,
    WRAPPER_SETTINGS,
    AVAILABLE_GAMES
)
from app.tools.utils import callback_blueprint  # Ensure this is correctly defined elsewhere
from app.tools.filter_keys import get_filter_keys
import importlib
import inspect


def create_dashboard_blueprint(training_manager, app_logger):  
    """
    Create the dashboard blueprint and integrate the training_manager and logger.

    :param training_manager: Global TrainingManager instance to interact with.
    :param app_logger: Global logger instance to be shared across blueprints.
    :return: Dashboard blueprint.
    """
    # Create a new logger for this blueprint
    logger = app_logger.__class__("dashboard_routes")  # Create a scoped logger

    # Initialize the dashboard blueprint
    dashboard_blueprint = Blueprint("dashboard", __name__)

    def dynamic_load_blueprints(module_name):
        """
        Dynamically load all blueprint instances from a module.
        """
        try:
            module = importlib.import_module(module_name)
            blueprints = {
                name: obj for name, obj in inspect.getmembers(module)
                if isinstance(obj, callback_blueprint)  # Ensure only callback_blueprint instances are loaded
            }
            logger.debug(f"Loaded blueprints from {module_name}: {list(blueprints.keys())}")
            return blueprints
        except Exception as e:
            logger.error(f"Error loading blueprints from {module_name}: {e}")
            return {}

    # Load blueprints for wrappers and callbacks dynamically
    wrapper_blueprints = dynamic_load_blueprints("app_wrappers")
    callback_blueprints = dynamic_load_blueprints("app_callbacks")

    @dashboard_blueprint.route("/dashboard/training", methods=["GET"])
    def training_dashboard():
        """
        Render the main training dashboard.
        """
        wrappers = [
            {
                "name": bp.name,
                "description": bp.description,
                "required": bp.required,
                "component_class": bp.component_class.__name__,
            }
            for bp in wrapper_blueprints.values()
        ]
        callbacks = [
            {
                "name": bp.name,
                "description": bp.description,
                "required": bp.required,
            }
            for bp in callback_blueprints.values()
        ]

        return render_template(
            "training_dashboard.html",
            title="Training Dashboard",
            hyperparameters=DEFAULT_HYPERPARAMETERS,
            training_config=DEFAULT_TRAINING_CONFIG,
            paths=DEFAULT_PATHS,
            env_settings=ENV_SETTINGS,  # Added env_settings
            wrapper_settings=WRAPPER_SETTINGS,  # Added wrapper_settings
            wrappers=wrappers,
            callbacks=callbacks,
            available_games=AVAILABLE_GAMES
        )
    
    @dashboard_blueprint.route("/update-game-id", methods=["POST"])
    def update_game_id():
        """
        Update the game_id in environment settings and dynamically adjust filter keys.
        """
        data = request.get_json()
        game_id = data.get("game_id")
        if not game_id or game_id not in AVAILABLE_GAMES:
            return jsonify({"error": "Invalid game ID"}), 400

        ENV_SETTINGS["game_id"] = game_id
        filter_keys = get_filter_keys(game_id, True)  # Dynamically update filter keys
        WRAPPER_SETTINGS["filter_keys"] = filter_keys

        return jsonify({"message": "Game ID updated", "filterKeys": filter_keys}), 200



    
    return dashboard_blueprint
