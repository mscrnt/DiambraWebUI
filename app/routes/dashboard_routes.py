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
from app.tools.utils import dynamic_load_blueprints
from app.tools.filter_keys import get_filter_keys
from app.tools.game_info import get_game_info


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



    # Load blueprints for wrappers and callbacks dynamically
    wrapper_blueprints = dynamic_load_blueprints("app.tools.app_wrappers")
    callback_blueprints = dynamic_load_blueprints("app.tools.app_callbacks")


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
            env_settings=ENV_SETTINGS,
            wrapper_settings=WRAPPER_SETTINGS,
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

    @dashboard_blueprint.route("/update_game_environment", methods=["POST"])
    def update_game_environment():
        """
        Updates game-specific environment settings based on the selected game ID.
        """
        try:
            data = request.get_json()
            game_id = data.get("game_id")

            if not game_id or game_id not in AVAILABLE_GAMES:
                logger.error(f"Invalid game ID received: {game_id}")
                return jsonify({"error": "Invalid game ID"}), 400

            # Update filter keys for the selected game
            filter_keys = get_filter_keys(game_id, True)
            WRAPPER_SETTINGS["filter_keys"] = filter_keys

            # Extract game-specific settings
            game_settings = get_game_info(game_id)
            if not game_settings:
                logger.error(f"Game ID not found: {game_id}")
                return jsonify({"error": "Game not found"}), 404

            resolution = game_settings.get("resolution", (0, 0, 0))
            frame_shapes = [
                {"value": f"{resolution[0]}, {resolution[1]}, {resolution[2]}", "label": f"Original ({resolution[0]}, {resolution[1]}, {resolution[2]})"},
                {"value": f"{resolution[0] // 2}, {resolution[1] // 2}, 3", "label": f"Small RGB ({resolution[0] // 2}, {resolution[1] // 2}, 3)"},
                {"value": f"{resolution[0] // 4}, {resolution[1] // 4}, 1", "label": f"Very Small Grayscale ({resolution[0] // 4}, {resolution[1] // 4}, 1)"},
            ]

            env_settings = {
                "difficulty": list(range(1, game_settings.get("max_difficulty", 8) + 1)),
                "frame_shape": frame_shapes,
                "outfits": [f"Outfit {i}" for i in range(1, game_settings.get("max_outfits", 1) + 1)],
                "num_characters": game_settings.get("num_characters"),
                "num_stages": game_settings.get("num_stages"),
                "moves": game_settings.get("moves"),
                "attacks": game_settings.get("attacks"),
                "n_players": list(range(1, game_settings.get("max_players", 2) + 1)),
            }

            logger.info(f"Final env_settings for {game_id}: {env_settings}")
            return jsonify({"env_settings": env_settings, "filter_keys": filter_keys}), 200

        except Exception as e:
            logger.error(f"Error updating game environment: {e}")
            return jsonify({"error": str(e)}), 500

        
    @dashboard_blueprint.route("/get_characters/<game_id>", methods=["GET"])
    def get_characters(game_id):
        """
        Fetch characters and game type for the given game ID.
        """
        try:
            game_data = get_game_info(game_id)
            if not game_data:
                return jsonify({"error": "Game not found"}), 404

            return jsonify({
                "gameType": game_data.get("game_type"),
                "characters": game_data.get("characters"),
            }), 200
        except Exception as e:
            logger.error(f"Error fetching characters for {game_id}: {e}")
            return jsonify({"error": str(e)}), 500


    return dashboard_blueprint
