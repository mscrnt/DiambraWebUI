# path: routes/training_routes.py

from flask import Blueprint, request, jsonify
import threading
from app import (
    DEFAULT_HYPERPARAMETERS,
    DEFAULT_TRAINING_CONFIG,
    DEFAULT_PATHS,
    ENV_SETTINGS,
    WRAPPER_SETTINGS,
    AVAILABLE_GAMES
)
from app.tools.filter_keys import get_filter_keys
from app.tools.utils import start_diambra_engine
import os
import subprocess
import tempfile
import json
import gc

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
        """
        Start the training process by preparing the training configuration and 
        launching the DIAMBRA CLI command to execute the training script.
        """
        global monitoring_thread
        global monitoring_active
        gc.collect()

        with training_lock:
            if training_manager.is_training_active():
                return jsonify({"status": "running", "message": "Training is already in progress."})

            try:
                # Retrieve and validate the incoming training data
                data = request.get_json() or {}
                logger.debug(f"Received training data: {json.dumps(data, indent=4)}")

                roms_path = data.get("roms_path", DEFAULT_PATHS["roms_path"])
                if not os.path.exists(roms_path):
                    return jsonify({"status": "error", "message": f"ROMs path does not exist: {roms_path}"}), 400

                num_envs = int(data.get("training_config", {}).get("num_envs", 1))
                if num_envs < 1:
                    return jsonify({"status": "error", "message": "Number of environments must be at least 1."}), 400

                # Update active training configuration
                training_manager.update_config({
                    "training_config": data.get("training_config", {}),
                    "hyperparameters": data.get("hyperparameters", {}),
                    "wrapper_settings": data.get("wrapper_settings", {}),
                    "env_settings": data.get("env_settings", {}),  # Add env_settings
                    "enabled_wrappers": data.get("wrappers", training_manager.get_active_config().get("enabled_wrappers", [])),
                    "enabled_callbacks": data.get("callbacks", training_manager.get_active_config().get("enabled_callbacks", [])),
                })

                # Prepare the configuration file
                active_config = training_manager.get_active_config()
                temp_config_file_path = os.path.join(os.getcwd(), "tmp", f"tmpfile_{os.getpid()}.json")
                os.makedirs(os.path.dirname(temp_config_file_path), exist_ok=True)

                with open(temp_config_file_path, 'w') as temp_config_file:
                    json.dump(active_config, temp_config_file, indent=4)
                logger.info(f"Temporary configuration file created: {temp_config_file_path}")

                # Construct the DIAMBRA CLI command
                python_executable = os.path.join(os.path.dirname(os.getcwd()), "venv", "Scripts", "python.exe")
                script_path = os.path.join(os.getcwd(), "training_script.py")
                command = [
                    "diambra", "run",
                    "-s", str(num_envs),
                    "--path.roms", roms_path,
                    "--interactive=false",
                    "--env.preallocateport",
                    python_executable, script_path, temp_config_file_path
                ]
                logger.info(f"DIAMBRA CLI command: {' '.join(command)}")

                # Define the log monitoring function
                def monitor_logs():
                    logger.info("Starting DIAMBRA CLI log monitoring...")
                    try:
                        with subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            encoding="utf-8"
                        ) as process:
                            for line in process.stdout:
                                if line.strip():
                                    logger.info(f"[diambra_cli] {line.strip()}")
                            process.wait()
                            if process.returncode != 0:
                                logger.error(f"DIAMBRA CLI exited with return code {process.returncode}.")
                    except Exception as e:
                        logger.error(f"Error monitoring logs: {str(e)}")
                    finally:
                        # Clean up the temporary configuration file
                        if os.path.exists(temp_config_file_path):
                            os.remove(temp_config_file_path)
                            logger.info(f"Temporary configuration file deleted: {temp_config_file_path}")

                # Start the log monitoring in a separate thread
                monitoring_active = True
                monitoring_thread = threading.Thread(target=monitor_logs, daemon=True)
                monitoring_thread.start()

                return jsonify({"status": "success", "message": "Training started using DIAMBRA CLI."})

            except Exception as e:
                logger.error(f"Error during training setup: {str(e)}", exc_info=True)
                return jsonify({"status": "error", "message": f"Failed to start training: {str(e)}"}), 500



    def stop_containers(container_names):
        """
        Stop the given list of Docker containers.

        :param container_names: List of container names to stop.
        """
        logger = app_logger.__class__("stop_containers")
        for container_name in container_names:
            try:
                logger.info(f"Stopping container: {container_name}...")
                subprocess.run(
                    ["docker", "stop", container_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False  # Use check=False to suppress errors if container is already stopped
                )
                logger.info(f"Container '{container_name}' stopped.")
            except Exception as e:
                logger.error(f"Error stopping container '{container_name}': {str(e)}")

    @training_blueprint.route("/stop_training", methods=["POST"])
    def stop_training():
        """Stop the training process and log monitoring."""
        global monitoring_thread
        global monitoring_active
        global training_thread
        global containers_to_stop

        with training_lock:
            if not training_manager.is_training_active():
                return jsonify({"status": "not_running", "message": "Training is not running."})

            try:
                # Stop log monitoring
                if monitoring_thread and monitoring_thread.is_alive():
                    logger.info("Stopping log monitoring thread...")
                    monitoring_active = False
                    monitoring_thread.join()
                    logger.info("Log monitoring stopped.")

                # Stop the training thread
                if training_thread and training_thread.is_alive():
                    logger.info("Waiting for training thread to complete...")
                    training_thread.join()
                    logger.info("Training thread stopped.")

                # Stop the training process
                training_manager.stop_training()
                logger.info("Training stop command executed.")

                # Stop all associated containers
                stop_containers(containers_to_stop)
                logger.info("All associated containers have been stopped.")

                return jsonify({"status": "success", "message": "Training and log monitoring stopped successfully."})
            except Exception as e:
                logger.error(f"Error stopping training: {e}")
                return jsonify({"status": "error", "message": f"Failed to stop training: {str(e)}"})

    @training_blueprint.route("/training_status", methods=["GET"]) 
    def training_status():
        """Return the current training status."""
        with training_lock:
            try:
                training_active = training_manager.is_training_active()
                logger.debug(f"Training status checked: active={training_active}")
                return jsonify({"training": training_active})
            except Exception as e:
                logger.error(f"Error checking training status: {e}") 
                return jsonify({"status": "error", "message": "Failed to check training status."}), 500

    @training_blueprint.route("/render_status", methods=["GET"])
    def render_status():
        """Check if rendering is active."""
        with training_lock:
            try:
                rendering = training_manager.render_manager.is_rendering() if training_manager.render_manager else False
                logger.debug(f"Render status checked: rendering={rendering}")
                return jsonify({"rendering": rendering})
            except Exception as e:
                logger.error(f"Error checking render status: {e}")
                return jsonify({"status": "error", "message": "Failed to check rendering status."}), 500
            
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
