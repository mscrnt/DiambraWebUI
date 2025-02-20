# path: .app/tools/utils.py

from app.log_manager import LogManager
from abc import ABC
from inspect import signature
import importlib
import inspect
import pickle
import os
import tempfile
from app import DEFAULT_HYPERPARAMETERS, DEFAULT_TRAINING_CONFIG, DEFAULT_PATHS, ENV_SETTINGS, WRAPPER_SETTINGS



# Initialize a logger specific to this module

app_logger = LogManager("utils")



class diambra_blueprint(ABC):
    """
    A universal blueprint for defining components like callbacks and wrappers.
    """

    def __init__(
        self,
        component_class,
        component_type,
        required=False,
        default_params=None,
        arg_map=None,
        name=None,
        description=None,
    ):
        if component_type not in {"callback", "wrapper"}:
            raise ValueError(f"Invalid component type: {component_type}. Must be 'callback' or 'wrapper'.")

        self.component_class = component_class
        self.component_type = component_type
        self.required = required
        self.default_params = default_params or {}
        self.arg_map = arg_map or {}
        self.name = name or component_class.__name__
        self.description = description or "No description provided."
        self.logger = app_logger.__class__("diambra_blueprint")

    def is_required(self):
        """Check if the blueprint is required."""
        return self.required

    def create_instance(self, config=None, env=None, **override_params):
        """
        Create an instance of the component with optional parameter overrides.

        :param config: Configuration dictionary to resolve dynamic arguments.
        :param env: Environment to be passed to wrappers that require it.
        :param override_params: Parameters to override the defaults.
        :return: An instance of the component.
        """
        # Combine default parameters with overrides
        params = {**self.default_params, **override_params}

        # Automatically resolve arguments based on the configuration and arg_map
        if config and self.arg_map:
            for arg_name, config_key in self.arg_map.items():
                if config_key in config and arg_name not in params:
                    params[arg_name] = config[config_key]

        # Convert numeric parameters to integers where necessary
        for key, value in params.items():
            if key in {"check_freq", "num_envs"} and isinstance(value, str) and value.isdigit():
                params[key] = int(value)

        # Add the `env` argument for wrappers
        if self.component_type == "wrapper" and "env" not in params:
            if env is None:
                self.logger.error(f"The 'env' argument is missing for wrapper {self.name}.")
                raise ValueError(f"The 'env' argument is required for wrapper {self.name}.")
            params["env"] = env

        # Validate arguments against the component's signature
        component_sig = signature(self.component_class)
        valid_params = {k: v for k, v in params.items() if k in component_sig.parameters}

        self.logger.debug(f"Creating {self.component_class.__name__} with parameters: {valid_params}")
        try:
            return self.component_class(**valid_params)
        except Exception as e:
            self.logger.error(f"Error instantiating {self.name}: {e}", exc_info=True)
            raise
    
def dynamic_load_blueprints(module_name):
    """
    Dynamically load all blueprint instances from a module with detailed logging.
    """
    logger = app_logger.__class__("dynamic_load_blueprints")
    try:
        # Import module based on the Python package path, not the file system
        module = importlib.import_module(module_name)
        blueprints = {
            name: obj for name, obj in inspect.getmembers(module)
            if isinstance(obj, diambra_blueprint)  # Ensure it's a diambra_blueprint instance
        }
        if blueprints:
            logger.info(f"Loaded blueprints from {module_name}: {list(blueprints.keys())}")
        else:
            logger.warning(f"No blueprints found in module: {module_name}")
        return blueprints
    except Exception as e:
        logger.error(f"Error loading blueprints from {module_name}: {e}", exc_info=True)
        return {}


def save_to_pickle(obj, filename, custom_dir=None):
    """Save an object to a pickle file in a specified directory."""
    logger = app_logger.__class__("save_to_pickle")
    try:
        # Use the custom directory if provided, otherwise fall back to system temp directory
        temp_dir = custom_dir or tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)  # Ensure the directory exists
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, "wb") as f:
            pickle.dump(obj, f)
        logger.info(f"Object saved to pickle file: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save object to {filename}: {e}")
        raise ValueError(f"Failed to save object to {filename}: {e}")
    

def apply_wrappers(env, selected_wrappers, blueprints):
    """
    Apply dynamically selected wrappers to the environment based on blueprints.

    :param env: The base environment to wrap.
    :param selected_wrappers: List of wrapper names to apply.
    :param blueprints: Dictionary of available wrapper blueprints.
    :return: Wrapped environment.
    """
    logger = LogManager("apply_wrappers")
    logger.info(f"Applying wrappers: {selected_wrappers}")

    for wrapper_name in selected_wrappers:
        blueprint = blueprints.get(wrapper_name)
        if blueprint:
            try:
                # Map arguments dynamically from the blueprint's argument map
                params = {"env": env}
                instance = blueprint.create_instance(**params)
                env = instance
                logger.info(f"Applied wrapper: {wrapper_name}")
            except Exception as e:
                logger.error(f"Failed to apply wrapper {wrapper_name}: {e}")
        else:
            logger.warning(f"Wrapper blueprint '{wrapper_name}' not found. Skipping.")
    return env


def initialize_callbacks(training_manager):
    logger = LogManager("initialize_callbacks")
    logger.info("Initializing callbacks...")
    callback_instances = []

    fallback_config = {
        **DEFAULT_TRAINING_CONFIG,
        **DEFAULT_HYPERPARAMETERS,
        **DEFAULT_PATHS,
        **ENV_SETTINGS,
        **WRAPPER_SETTINGS,
    }

    enabled_callbacks = training_manager.active_config["config"].get("enabled_callbacks", [])
    logger.debug(f"Enabled callbacks: {enabled_callbacks}")

    for cb_name in enabled_callbacks:
        blueprint = next(
            (bp for key, bp in training_manager.callback_blueprints.items()
             if key == cb_name or bp.name == cb_name),
            None
        )

        if blueprint:
            logger.debug(f"Found blueprint for callback '{cb_name}': {blueprint}")

            try:
                params = {
                    key: (
                        training_manager.active_config["config"]["training_config"].get(value)
                        or fallback_config.get(value)
                    )
                    for key, value in blueprint.arg_map.items()
                    if value in training_manager.active_config["config"]["training_config"]
                    or value in fallback_config
                }

                # Convert numeric parameters where needed
                for param_key, param_value in params.items():
                    if param_key in {"check_freq", "num_envs"}:
                        try:
                            params[param_key] = int(param_value)
                        except ValueError as e:
                            logger.error(f"Invalid value for '{param_key}': {param_value}. Must be an integer. Error: {e}")
                            raise

                # Log resolved parameters
                logger.debug(f"Initializing callback '{cb_name}' with parameters: {params}")
                instance = blueprint.create_instance(**params)
                callback_instances.append(instance)
                logger.info(f"Initialized callback: {cb_name} with params: {params}")

            except Exception as e:
                logger.error(f"Failed to initialize callback '{cb_name}': {e}", exc_info=True)
        else:
            logger.warning(f"Callback blueprint '{cb_name}' not found. Skipping.")

    training_manager.callback_instances = callback_instances
    logger.info("Callbacks initialized successfully.")


def load_from_pickle(file_path):
    """Load an object from a pickle file."""
    logger = app_logger.__class__("load_from_pickle")
    try:
        with open(file_path, "rb") as f:
            obj = pickle.load(f)
        logger.info(f"Object loaded from pickle file: {file_path}")
        return obj
    except Exception as e:
        logger.error(f"Failed to load object from {file_path}: {e}")
        raise RuntimeError(f"Failed to load object from {file_path}: {e}")
    
def filter_config(config, allowed_keys):
    """
    Filter out keys that are not part of the allowed keys.
    :param config: Dictionary of configuration.
    :param allowed_keys: Set of allowed keys.
    :return: Filtered dictionary.
    """
    return {key: config[key] for key in config if key in allowed_keys}

