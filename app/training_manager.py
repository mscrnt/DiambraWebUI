# path: ./app/training_manager.py

from app import DEFAULT_TRAINING_CONFIG, DEFAULT_HYPERPARAMETERS, ENV_SETTINGS, WRAPPER_SETTINGS
from app.render_manager import RenderManager
from app.log_manager import LogManager
from app.tools.utils import dynamic_load_blueprints, filter_config
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CallbackList
from diambra.arena import load_settings_flat_dict, SpaceTypes
from diambra.arena.stable_baselines3.make_sb3_env import make_sb3_env, EnvironmentSettings, WrappersSettings
from diambra.arena.stable_baselines3.sb3_utils import linear_schedule
import threading
import json

logger = LogManager("TrainingManager")

class TrainingManager:
    def __init__(self, config=None):
        """
        Initialize the TrainingManager.

        :param config: Configuration for training.
        """
        # Load blueprints dynamically
        self.wrapper_blueprints = dynamic_load_blueprints("app.tools.app_wrappers")
        self.callback_blueprints = dynamic_load_blueprints("app.tools.app_callbacks")

        # Initialize default configuration
        self.default_config = self.get_default_config(
            wrapper_blueprints=self.wrapper_blueprints,
            callback_blueprints=self.callback_blueprints,
            
        )

        # Use provided or default configuration
        self.config = config or self.default_config

        # Initialize active configuration
        self.active_config = {"config": None, "use_active": False}

        # Other attributes
        self.training_active_event = threading.Event()
        self.training_active_event.clear()
        self.model_updated_flag = threading.Event()
        self.model_updated_flag.clear()
        self.render_manager = None
        self.model = None
        self.env = None
        self.num_envs = int(self.config["training_config"].get("num_envs", 1))
        self.render_env_num_envs = 1
        self.wrapper_blueprints = {}
        self.callback_blueprints = {}
        self.callback_instances = []
        self.selected_wrappers = []
        self.load_blueprints = dynamic_load_blueprints
        self.shader_settings = {
            "radial_distortion": False,
            "scanlines": False,
            "dot_mask": False,
            "rolling_lines": False,
            "gamma_correction": False,
        }
        
    def get_shader_settings(self):
        """Get the current shader settings."""
        return self.shader_settings

    def toggle_shader(self, key, enabled):
        """Toggle a specific shader setting."""
        if key not in self.shader_settings:
            raise ValueError(f"Invalid shader key: {key}")
        self.shader_settings[key] = enabled

    def toggle_all_shaders(self, enable_all):
        """Enable or disable all shader settings."""
        for key in self.shader_settings:
            self.shader_settings[key] = enable_all

    def __getstate__(self):
        """Prepare the state for pickling."""
        state = self.__dict__.copy()
        # Serialize callbacks for later reconstruction
        state["serialized_callbacks"] = [
            {
                "name": blueprint.name,
                "module": blueprint.component_class.__module__,
                "class_name": blueprint.component_class.__name__,
                "params": {
                    **blueprint.default_params,
                    **self.config.get("training_config", {}).get("callbacks_params", {}).get(blueprint.name, {})
                }
            }
            for name, blueprint in self.callback_blueprints.items()
            if name in self.config.get("enabled_callbacks", [])
        ]
        # Remove non-pickleable objects
        state.pop("render_manager", None)
        state.pop("model", None)
        state.pop("env", None)
        state.pop("training_active_event", None)
        state.pop("model_updated_flag", None)
        return state

    def __setstate__(self, state):
        """Restore the state from unpickling."""
        self.__dict__.update(state)
        self.render_manager = None
        self.model = None
        self.env = None
        self.training_active_event = threading.Event()
        self.training_active_event.clear()
        self.model_updated_flag = threading.Event()
        self.model_updated_flag.clear()

        # Dynamically reload callback instances
        self.callback_instances = []
        for cb in self.config.get("serialized_callbacks", []):
            blueprint = self.callback_blueprints.get(cb["name"])
            if blueprint:
                try:
                    self.callback_instances.append(
                        blueprint.create_instance(**cb["params"])
                    )
                except Exception as e:
                    logger.error(f"Failed to initialize callback {cb['name']}: {e}")


    def set_active_config(self, config):
        """Set the active configuration, ensuring all fields are properly updated."""
        try:
            # Validate critical fields like game_id
            if "game_id" not in config.get("training_config", {}):
                raise ValueError("Missing 'game_id' in training configuration.")

            # Merge the new configuration with defaults to ensure completeness
            self.active_config = {
                "config": {
                    "training_config": {**self.default_config["training_config"], **config.get("training_config", {})},
                    "hyperparameters": {**self.default_config["hyperparameters"], **config.get("hyperparameters", {})},
                    "wrapper_settings": {**self.default_config["wrapper_settings"], **config.get("wrapper_settings", {})},
                    "env_settings": {**self.default_config["env_settings"], **config.get("env_settings", {})},
                    "enabled_wrappers": config.get("enabled_wrappers", self.default_config["enabled_wrappers"]),
                    "enabled_callbacks": config.get("enabled_callbacks", self.default_config["enabled_callbacks"]),
                },
                "use_active": True,
            }

            logger.info("Active configuration updated successfully.")
            logger.debug(f"Active configuration: {json.dumps(self.active_config['config'], indent=4)}")

        except Exception as e:
            logger.error(f"Failed to set active configuration: {str(e)}", exc_info=True)
            raise

    def get_active_config(self):
        """
        Retrieve the active configuration.
        If no active configuration exists, return the default.
        """
        try:
            if self.active_config["use_active"]:
                logger.debug("Returning active configuration.")
                return self.active_config["config"]
            else:
                logger.debug("Returning default configuration as no active configuration is set.")
                return self.default_config
        except KeyError as e:
            logger.error(f"Error retrieving active configuration: {str(e)}")
            return self.default_config



    def clear_active_config(self):
        """Clear the active configuration and reset to default."""
        self.active_config = {"config": None, "use_active": False}
        logger.info("Active configuration cleared.")

    def get_effective_config(self):
        """
        Determine the effective configuration to use: 
        active configuration if available, otherwise default.
        """
        return self.get_active_config() if self.active_config["use_active"] else self.default_config


    @staticmethod
    def get_default_config(wrapper_blueprints=None, callback_blueprints=None):
        """Return the default training configuration with required wrappers and callbacks."""
        # Fallback to empty dictionaries if blueprints are not provided
        wrapper_blueprints = wrapper_blueprints or {}
        callback_blueprints = callback_blueprints or {}

        # Identify required wrappers and callbacks
        required_wrappers = [
            name for name, blueprint in wrapper_blueprints.items() if blueprint.is_required()
        ]
        required_callbacks = [
            name for name, blueprint in callback_blueprints.items() if blueprint.is_required()
        ]

        # Return the default configuration with required components
        return {
            "training_config": DEFAULT_TRAINING_CONFIG.copy(),
            "hyperparameters": DEFAULT_HYPERPARAMETERS.copy(),
            "enabled_wrappers": required_wrappers,
            "enabled_callbacks": required_callbacks,
            "wrapper_settings": WRAPPER_SETTINGS.copy(),
            "env_settings": ENV_SETTINGS.copy(),
        }

    def stop_training(self):
        """Stop training and rendering gracefully."""
        logger.info("Stopping training...")
        self.training_active_event.clear()
        if self.render_manager:
            self.render_manager.stop()
        logger.info("Training stopped.")

    def is_training_active(self):
        """Check if training is active."""
        return self.training_active_event.is_set()

    def is_model_updated(self):
        """Check if the model has been updated."""
        return self.model_updated_flag.is_set()

    def clear_model_updated(self):
        """Clear the model updated flag."""
        self.model_updated_flag.clear()

    def set_model_updated(self):
        """Set the model updated flag."""
        self.model_updated_flag.set()

    def initialize_training(self):
        """Initialize training configurations, environments, and the model."""
        logger.debug("Initializing training with config", extra={"config": self.config})
        logger.debug(f"Using loaded wrapper blueprints: {list(self.wrapper_blueprints.keys())}")
        logger.debug(f"Using loaded callback blueprints: {list(self.callback_blueprints.keys())}")

        # Load the active configuration
        self.config = self.get_active_config()

        game_id = self.config["training_config"].get("game_id")
        if not game_id:
            raise ValueError("Game ID is missing or invalid in the training configuration.")

        # Merge and parse user configuration
        self._merge_and_parse_config()

        # Initialize callbacks and wrappers
        self._initialize_callbacks_and_wrappers()

        # Initialize environments and model
        self._initialize_environments_and_model()

        # Initialize the RenderManager
        self.render_manager = RenderManager(
            render_env=self.render_env,
            model=self.model,
            training_active_flag=self.is_training_active,
            model_updated_flag=self.model_updated_flag,
            shader_settings_flag=lambda: self.shader_settings,  # Dynamically fetch shader states
        )

    def update_config(self, new_config):
        """Update the training configuration with a new configuration."""
        try:
            # Ensure all necessary keys exist in the configuration
            self.config.setdefault("training_config", {})
            self.config.setdefault("hyperparameters", {})
            self.config.setdefault("wrapper_settings", {})
            self.config.setdefault("env_settings", {})
            self.config.setdefault("enabled_wrappers", [])
            self.config.setdefault("enabled_callbacks", [])

            # Update the configuration fields
            self.config["training_config"].update(new_config.get("training_config", {}))
            self.config["hyperparameters"].update(new_config.get("hyperparameters", {}))
            self.config["wrapper_settings"].update(new_config.get("wrapper_settings", {}))
            self.config["env_settings"].update(new_config.get("env_settings", {}))
            self.config["enabled_wrappers"] = new_config.get("enabled_wrappers", self.config["enabled_wrappers"])
            self.config["enabled_callbacks"] = new_config.get("enabled_callbacks", self.config["enabled_callbacks"])

            # Validate critical fields like game_id
            game_id = self.config["training_config"].get("game_id")
            if not game_id:
                raise ValueError("Missing 'game_id' in training configuration. Ensure it is set before starting training.")

            # Save this as the active configuration
            self.set_active_config(self.config)
            logger.info("Training configuration updated successfully.")
        except Exception as e:
            logger.error("Failed to update configuration", exc_info=True)
            raise ValueError("Invalid configuration format or data")


    def _merge_and_parse_config(self):
        """
        Merge and parse user-provided configurations with default environment and wrapper settings.
        Ensure it always returns a valid configuration.
        """
        try:
            # Start with global defaults
            training_config = {**ENV_SETTINGS, **self.config.get("training_config", {})}
            wrapper_settings = {**WRAPPER_SETTINGS, **self.config.get("wrapper_settings", {})}
            hyperparameters = {**DEFAULT_HYPERPARAMETERS, **self.config.get("hyperparameters", {})}

            # Handle special fields like `action_space`
            if "action_space" in training_config:
                action_space_str = training_config["action_space"].upper()
                if action_space_str == "DISCRETE":
                    training_config["action_space"] = SpaceTypes.DISCRETE
                elif action_space_str == "MULTI_DISCRETE":
                    training_config["action_space"] = SpaceTypes.MULTI_DISCRETE
                else:
                    raise ValueError(f"Invalid action_space: {training_config['action_space']}")

            # Process numeric or None fields
            for key, value in training_config.items():
                if value in ("None", None, ""):
                    training_config[key] = None
                elif isinstance(value, str) and value.replace(".", "", 1).isdigit():
                    training_config[key] = float(value) if "." in value else int(value)

            for key, value in hyperparameters.items():
                if value in ("None", None, ""):
                    hyperparameters[key] = None
                elif isinstance(value, str) and value.replace(".", "", 1).isdigit():
                    hyperparameters[key] = float(value) if "." in value else int(value)

            # Add dynamic schedules for learning rate and clipping ranges
            hyperparameters["learning_rate"] = linear_schedule(
                hyperparameters.get("learning_rate_start", 0.00025),
                hyperparameters.get("learning_rate_end", 0.0000025),
            )
            hyperparameters["clip_range"] = linear_schedule(
                hyperparameters.get("clip_range_start", 0.15),
                hyperparameters.get("clip_range_end", 0.025),
            )

            if hyperparameters.get("clip_range_vf_start") is not None and hyperparameters.get("clip_range_vf_end") is not None:
                hyperparameters["clip_range_vf"] = linear_schedule(
                    hyperparameters["clip_range_vf_start"],
                    hyperparameters["clip_range_vf_end"],
                )

            # Finalize and return the merged configuration
            config = {
                "training_config": training_config,
                "wrapper_settings": wrapper_settings,
                "hyperparameters": hyperparameters,
                "enabled_wrappers": self.config.get("enabled_wrappers", []),
                "enabled_callbacks": self.config.get("enabled_callbacks", []),
            }
            logger.info("Configuration successfully merged and parsed.")
            return config

        except Exception as e:
            logger.error(f"Error merging and parsing configuration: {e}", exc_info=True)
            # Fallback to default configuration if there's an error
            return {
                "training_config": ENV_SETTINGS.copy(),
                "wrapper_settings": WRAPPER_SETTINGS.copy(),
                "hyperparameters": DEFAULT_HYPERPARAMETERS.copy(),
                "enabled_wrappers": self.config.get("enabled_wrappers", []),
                "enabled_callbacks": self.config.get("enabled_callbacks", []),
            }



    def _initialize_callbacks_and_wrappers(self):
        """Initialize selected wrappers and callbacks."""
        logger.debug(f"Config data: {self.config}")

        # Initialize callbacks
        enabled_callbacks = set(self.config.get("enabled_callbacks", []))
        required_callbacks = {
            name for name, blueprint in self.callback_blueprints.items() if blueprint.is_required()
        }
        enabled_callbacks.update(required_callbacks)  # Ensure required callbacks are always included

        logger.info(f"Enabled callbacks from config: {enabled_callbacks}")
        self.callback_instances = []
        serialized_callbacks = []  # To store callback details for reconstruction

        for name, blueprint in self.callback_blueprints.items():
            if name in enabled_callbacks:
                logger.debug(f"Initializing callback: {blueprint.name}")
                try:
                    # Create the callback instance
                    callback_instance = blueprint.create_instance(config=self.config, training_manager=self)
                    self.callback_instances.append(callback_instance)

                    # Serialize the callback for reconstruction
                    serialized_callbacks.append({
                        "module": blueprint.component_class.__module__,
                        "class_name": blueprint.component_class.__name__,
                        "params": {**blueprint.default_params},  # Include default params
                    })
                except Exception as e:
                    logger.error(f"Failed to initialize callback '{name}': {e}")
            else:
                logger.warning(f"Callback '{blueprint.name}' not selected or not required. Skipping.")

        if not self.callback_instances:
            logger.warning("No valid callbacks initialized. Training will proceed without callbacks.")

        # Store serialized callbacks for later reconstruction
        self.config["serialized_callbacks"] = serialized_callbacks
        logger.debug(f"Serialized Callbacks: {json.dumps(serialized_callbacks, indent=4)}")


    def _initialize_environments_and_model(self):
        """Initialize the environment and the model."""
        try:
            # Filter training_config for valid EnvironmentSettings fields
            valid_env_keys = set(EnvironmentSettings.__annotations__.keys())
            filtered_training_config = filter_config(self.config["training_config"], valid_env_keys)

            # Filter hyperparameters for valid WrappersSettings fields
            valid_wrapper_keys = set(WrappersSettings.__annotations__.keys())
            filtered_wrapper_config = filter_config(self.config["hyperparameters"], valid_wrapper_keys)

            logger.debug(f"Filtered training configuration: {filtered_training_config}")
            logger.debug(f"Filtered wrapper configuration: {filtered_wrapper_config}")

            # Create render environment
            self.render_env, self.render_env_num_envs = make_sb3_env(
                self.config["training_config"]["game_id"],
                load_settings_flat_dict(EnvironmentSettings, filtered_training_config),
                load_settings_flat_dict(WrappersSettings, filtered_wrapper_config),
            )

            # Create training environments
            self.env, self.num_envs = make_sb3_env(
                self.config["training_config"]["game_id"],
                load_settings_flat_dict(EnvironmentSettings, filtered_training_config),
                load_settings_flat_dict(WrappersSettings, filtered_wrapper_config),
            )

            # Create PPO model
            self.model = PPO(
                "MultiInputPolicy",
                self.env,
                verbose=1,
                gamma=self.config["hyperparameters"]["gamma"],
                n_steps=self.config["hyperparameters"]["n_steps"],
                batch_size=self.config["hyperparameters"]["batch_size"],
                n_epochs=self.config["hyperparameters"]["n_epochs"],
                learning_rate=self.config["hyperparameters"]["learning_rate"],
                clip_range=self.config["hyperparameters"]["clip_range"],
                clip_range_vf=self.config["hyperparameters"].get("clip_range_vf"),
                normalize_advantage=self.config["hyperparameters"]["normalize_advantage"],
                ent_coef=self.config["hyperparameters"]["ent_coef"],
                vf_coef=self.config["hyperparameters"]["vf_coef"],
                max_grad_norm=self.config["hyperparameters"]["max_grad_norm"],
                policy_kwargs=self.config["hyperparameters"]["policy_kwargs"],
                target_kl=self.config["hyperparameters"]["target_kl"],
                tensorboard_log=self.config["training_config"]["tensorboard_log"],
                seed=self.config["hyperparameters"]["seed"],
                device=self.config["hyperparameters"]["device"],
            )
        except Exception as e:
            logger.error("Error initializing environments or model.", exc_info=True)
            raise


    def start_training(self):
        """Start the training loop and rendering."""
        logger.info("Starting training process...")
        self.training_active_event.set()
        try:
            self.render_manager.start()
            logger.debug(f"Training loop active: {self.is_training_active()}")
            self.model.learn(
                total_timesteps=self.config.get("total_timesteps", 32000000),
                callback=CallbackList(self.callback_instances),
            )
        except Exception as e:
            logger.error(f"An error occurred during training: {e}")
        finally:
            self.stop_training()
