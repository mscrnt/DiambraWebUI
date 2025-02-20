# path: routes/training_routes.py

from flask import Blueprint, request, jsonify
import threading
from app import (
    DEFAULT_PATHS,
    ENV_SETTINGS,
    AVAILABLE_GAMES
)
from app.tools.filter_keys import get_filter_keys
import os
import subprocess
import json
import gc
from app.tools.utils import save_to_pickle
import platform
from datetime import datetime
from app.container_manager import ContainerManager

# Initialize managers
training_container_manager = ContainerManager("training", log_file="logs/training_containers.log")
rendering_container_manager = ContainerManager("rendering", log_file="logs/rendering_containers.log")

enable_crt_shader = False


def create_training_blueprint(training_manager, app_logger, ):
    """
    Create the training blueprint and integrate the training_manager, logger, and db_manager.

    :param training_manager: Global TrainingManager instance to interact with.
    :param app_logger: Global logger instance to be shared across blueprints.
    :param db_manager: Database manager instance to provide database access.
    :return: Training blueprint.
    """
    # Scoped logger
    logger = app_logger.__class__("training_routes")



    training_blueprint = Blueprint("training_routes", __name__)

    # Shared state for training
    training_thread = None
    training_lock = threading.Lock()  # Ensure thread-safe access to training_manager

    def serialize_config(config):
        """Prepare the configuration dictionary for JSON serialization."""
        def safe_serialize(value):
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                return value
            if callable(value):
                return value.__name__
            return str(value)  # Fallback for non-serializable types

        # Ensure defaults and serialize
        serialized_config = {
            "training_config": config.get("training_config", {}),
            "hyperparameters": config.get("hyperparameters", {}),
            "enabled_wrappers": config.get("enabled_wrappers", []),
            "enabled_callbacks": config.get("enabled_callbacks", []),
        }
        return {key: safe_serialize(value) for key, value in serialized_config.items()}
    
    @training_blueprint.route("/start_training", methods=["POST"])
    def start_training():
        """Start the training process."""
        gc.collect()  # Run garbage collection to free up memory

        with training_lock:
            if training_container_manager.is_monitoring():
                return jsonify({"status": "running", "message": "Training is already in progress."})

            try:
                # Parse request data
                data = request.get_json() or {}
                logger.debug(f"Received training data: {json.dumps(data, indent=4)}")

                # Validate number of environments
                num_envs = int(data.get("training_config", {}).get("num_envs", 1))
                if num_envs < 1:
                    return jsonify({"status": "error", "message": "Number of environments must be at least 1."}), 400

                # Update training configuration
                updated_config = {
                    "training_config": data.get("training_config", {}),
                    "hyperparameters": data.get("hyperparameters", {}),
                    "wrapper_settings": data.get("wrapper_settings", {}),
                    "env_settings": data.get("env_settings", {}),
                    "enabled_wrappers": data.get(
                        "wrappers", training_manager.get_active_config().get("enabled_wrappers", [])
                    ),
                    "enabled_callbacks": data.get(
                        "callbacks", training_manager.get_active_config().get("enabled_callbacks", [])
                    ),
                }

                logger.debug("Updating training configuration with:")
                logger.debug(json.dumps(updated_config, indent=4))
                training_manager.update_config(updated_config)

                # Validate active configuration
                active_config = training_manager.get_active_config()
                if not active_config:
                    logger.error("No valid active configuration found in TrainingManager.")
                    return jsonify({"status": "error", "message": "Failed to set active training configuration."}), 500

                logger.info("Training configuration successfully updated.")
                logger.info(json.dumps(active_config, indent=4))

                # Save the updated TrainingManager state
                temp_dir = os.path.join(os.getcwd(), "tmp")
                pickle_path = save_to_pickle(training_manager, "training_manager_snapshot.pkl", custom_dir=temp_dir)
                logger.info(f"TrainingManager state saved to {pickle_path}")

                # Define script paths
                training_script_path = os.path.join(os.getcwd(), "training_script.py")
                rendering_script_path = os.path.join(os.getcwd(), "render_script.py")

                # Start training containers
                training_container_manager.start_container(
                    container_group="training_group",
                    script_path=training_script_path,
                    num_envs=num_envs
                )

                # Start rendering container
                rendering_container_manager.start_container(
                    container_group="render_group",
                    script_path=training_script_path,
                    num_envs=1  # Fixed to 1 for rendering
                )

                return jsonify({"status": "success", "message": "Training and rendering containers started successfully."})

            except Exception as e:
                logger.error(f"Error during training setup: {str(e)}", exc_info=True)
                return jsonify({"status": "error", "message": f"Failed to start training: {str(e)}"}), 500


    @training_blueprint.route("/stop_training", methods=["POST"])
    def stop_training():
        """Stop the training and rendering processes."""
        with training_lock:
            # Check if the training process is currently active
            if not training_container_manager.is_monitoring():
                return jsonify({"status": "not_running", "message": "Training is not running."})

            try:
                # Stop training containers
                logger.info("Stopping training containers...")
                training_container_manager.stop_container("training_group")
                
                # Stop rendering containers
                logger.info("Stopping rendering containers...")
                rendering_container_manager.stop_container("render_group")

                return jsonify({"status": "success", "message": "Training and rendering processes stopped successfully."})

            except Exception as e:
                logger.error(f"Error stopping training: {str(e)}", exc_info=True)
                return jsonify({"status": "error", "message": f"Failed to stop training: {str(e)}"}), 500


    @training_blueprint.route("/training_status", methods=["GET"])
    def training_status():
        """Return the current training status."""
        try:
            is_training_active = training_container_manager.is_monitoring()
            logger.debug(f"Training status checked: {'Running' if is_training_active else 'Stopped'}")
            return jsonify({"training": is_training_active})
        except Exception as e:
            logger.error(f"Error fetching training status: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "message": f"Failed to fetch training status: {str(e)}"}), 500


    @training_blueprint.route("/render_status", methods=["GET"])
    def render_status():
        """Check if rendering is active."""
        try:
            is_rendering_active = rendering_container_manager.is_monitoring()
            logger.debug(f"Rendering status checked: {'Active' if is_rendering_active else 'Inactive'}")
            return jsonify({"rendering": is_rendering_active})
        except Exception as e:
            logger.error(f"Error fetching render status: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "message": f"Failed to fetch rendering status: {str(e)}"}), 500
    
    @training_blueprint.route('/shader_status', methods=['GET'])
    def shader_status():
        """Return current shader settings.""" 
        try:
            return jsonify(shaderSettings=training_manager.get_shader_settings())
        except Exception as e:
            logger.error(f"Error fetching shader settings: {e}")
            return jsonify(error=str(e)), 500

    @training_blueprint.route('/toggle_shader', methods=['POST'])
    def toggle_shader():
        """Toggle a specific shader."""
        data = request.json
        key = data.get('key')
        enabled = data.get('enabled', False)

        try:
            training_manager.toggle_shader(key, enabled)
            logger.info(f"Shader '{key}' toggled: {'enabled' if enabled else 'disabled'}")
            return jsonify(success=True)
        except ValueError as e:
            logger.error(f"Invalid shader key: {key}")
            return jsonify(success=False, error=str(e)), 400
        except Exception as e:
            logger.error(f"Error toggling shader '{key}': {e}")
            return jsonify(success=False, error=str(e)), 500


    @training_blueprint.route('/toggle_shader_all', methods=['POST'])
    def toggle_shader_all():
        """Toggle all shaders."""
        data = request.json
        enable_all = data.get('enableAll', False)

        try:
            training_manager.toggle_all_shaders(enable_all)
            logger.info(f"All shaders toggled: {'enabled' if enable_all else 'disabled'}")
            return jsonify(success=True)
        except Exception as e:
            logger.error(f"Error toggling all shaders: {e}")
            return jsonify(success=False, error=str(e)), 500



    @training_blueprint.route("/model_status", methods=["GET"])
    def model_status():
        """Check if the model has been updated."""
        with training_lock:
            try:
                model_updated = training_manager.is_model_updated()
                logger.debug(f"Model status checked: updated={model_updated}")
                return jsonify({"model_updated": model_updated})
            except Exception as e:
                logger.error(f"Error checking model status: {e}")
                return jsonify({"status": "error", "message": "Failed to check model status."}), 500
            
    @training_blueprint.route("/current_config", methods=["GET"])
    def get_current_config():
        """Return the active or default training configuration.""" 
        with training_lock:
            try:
                current_config = training_manager.get_active_config()
                return jsonify({"status": "success", "config": current_config})
            except Exception as e:
                logger.error(f"Error fetching current configuration: {e}")
                return jsonify({"status": "error", "message": "Failed to fetch configuration."}), 500
            
    @training_blueprint.route("/reset_to_default", methods=["POST"])
    def reset_to_default():
        """Reset the active configuration to default."""
        with training_lock:
            try:
                training_manager.clear_active_config()
                return jsonify({"status": "success", "message": "Configuration reset to default."})
            except Exception as e:
                logger.error(f"Error resetting configuration: {e}")
                return jsonify({"status": "error", "message": "Failed to reset configuration."}), 500


    @training_blueprint.route("/update_game_environment", methods=["POST"])
    def update_game_environment():
        try:
            data = request.get_json()
            game_id = data.get("game_id")
            if not game_id:
                raise ValueError("Game ID is required.")

            # Fetch and validate environment settings for the selected game
            if game_id not in AVAILABLE_GAMES:
                raise ValueError(f"Game ID '{game_id}' is not recognized.")

            # Dynamically update ENV_SETTINGS based on the selected game
            ENV_SETTINGS.update({
                "game_id": game_id,
                "difficulty": AVAILABLE_GAMES[game_id].get("difficulty", []),
                "frame_shape": AVAILABLE_GAMES[game_id].get("frame_shape", []),
                "filter_keys": get_filter_keys(game_id),
            })

            return jsonify({"status": "success", "env_settings": ENV_SETTINGS, "filter_keys": ENV_SETTINGS["filter_keys"]})
        except Exception as e:
            logger.error(f"Error updating game environment: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400


    return training_blueprint
