# path: ./utils.py

from app.log_manager import LogManager
from abc import ABC
from inspect import signature


# Initialize a logger specific to this module
logger = LogManager("utils")


class callback_blueprint(ABC):
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

        # Add the `env` argument for wrappers
        if self.component_type == "wrapper":
            logger.debug(f"Checking env argument for wrapper {self.name}")
            if env is None:
                logger.error(f"The 'env' argument is missing for wrapper {self.name}.")
                raise ValueError(f"The 'env' argument is required for wrapper {self.name}.")
            params["env"] = env

        # Validate arguments against the component's signature
        component_sig = signature(self.component_class)
        valid_params = {k: v for k, v in params.items() if k in component_sig.parameters}

        # Debug: Log final parameters passed to the component
        logger.debug(f"Creating {self.component_class.__name__} with parameters: {valid_params}")
        return self.component_class(**valid_params)