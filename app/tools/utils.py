# path: .app/tools/utils.py

from app.log_manager import LogManager
from abc import ABC
from inspect import signature
import importlib
import inspect
import subprocess
import os
from app import DEFAULT_PATHS
import threading
import time
import grpc


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

        # Add the `env` argument for wrappers
        if self.component_type == "wrapper":
            self.logger.debug(f"Checking env argument for wrapper {self.name}")
            if env is None:
                self.logger.error(f"The 'env' argument is missing for wrapper {self.name}.")
                raise ValueError(f"The 'env' argument is required for wrapper {self.name}.")
            params["env"] = env

        # Validate arguments against the component's signature
        component_sig = signature(self.component_class)
        valid_params = {k: v for k, v in params.items() if k in component_sig.parameters}

        # Debug: Log final parameters passed to the component
        self.logger.debug(f"Creating {self.component_class.__name__} with parameters: {valid_params}")
        return self.component_class(**valid_params)
    
def dynamic_load_blueprints(module_name):
    """
    Dynamically load all blueprint instances from a module.
    """
    logger = app_logger.__class__("dynamic_load_blueprints")
    try:
        # Import module based on the Python package path, not the file system
        module = importlib.import_module(module_name)
        blueprints = {
            name: obj for name, obj in inspect.getmembers(module)
            if isinstance(obj, diambra_blueprint)  # Ensure it's a diambra_blueprint instance
        }
        logger.debug(f"Loaded blueprints from {module_name}: {list(blueprints.keys())}")
        return blueprints
    except Exception as e:
        logger.error(f"Error loading blueprints from {module_name}: {e}")
        return {}


def filter_config(config, allowed_keys):
    """
    Filter out keys that are not part of the allowed keys.
    :param config: Dictionary of configuration.
    :param allowed_keys: Set of allowed keys.
    :return: Filtered dictionary.
    """
    return {key: config[key] for key in config if key in allowed_keys}


def is_diambra_engine_running(container_name="diambra_engine"):
    """
    Check if the DIAMBRA Engine container is running.

    :param container_name: Name of the Docker container to check.
    :return: True if the container is running, False otherwise.
    """
    logger = app_logger.__class__("is_diambra_engine_running")
    try:
        logger.info(f"Checking if container '{container_name}' is running...")
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"Error checking container status: {result.stderr.strip()}")
            return False
        running_containers = result.stdout.strip().split("\n")
        is_running = container_name in running_containers
        logger.info(f"Container '{container_name}' running: {is_running}")
        return is_running
    except Exception as e:
        logger.error(f"Error checking DIAMBRA Engine container: {e}")
        return False
    

def is_grpc_ready(address="localhost", port=50051, timeout=30):
    """
    Check if the gRPC server at the specified address is ready.

    :param address: The gRPC server address (default: "localhost").
    :param port: The gRPC server port (default: 50051).
    :param timeout: Time in seconds to wait for readiness.
    :return: True if the server is ready, False otherwise.
    """
    logger = app_logger.__class__("is_grpc_ready")
    grpc_address = f"{address}:{port}"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            channel = grpc.insecure_channel(grpc_address)
            grpc.channel_ready_future(channel).result(timeout=2)
            logger.info(f"gRPC server at {grpc_address} is ready.")
            return True
        except grpc.FutureTimeoutError:
            logger.info(f"gRPC server at {grpc_address} is not ready. Retrying...")
            time.sleep(1)
    logger.error(f"gRPC server at {grpc_address} did not become ready in time.")
    return False


def start_diambra_engine(roms_path=None, container_name="diambra_engine", grpc_port=50051, host_port=None):
    """
    Start a DIAMBRA Engine using Docker, map the gRPC port, and ensure its server is ready.

    :param roms_path: Path to the ROMs directory. Defaults to the value in DEFAULT_PATHS.
    :param container_name: Name to assign to the Docker container.
    :param grpc_port: Port inside the container for the gRPC server (default: 50051).
    :param host_port: Port on the host to map to the container's gRPC port.
    :return: True if the DIAMBRA Engine starts successfully and its server is ready, False otherwise.
    """
    logger = app_logger.__class__("start_diambra_engine")
    roms_path = roms_path or DEFAULT_PATHS["roms_path"]
    credentials_path = os.path.expanduser(DEFAULT_PATHS["credentials_file"])
    host_port = host_port or grpc_port  # Default to grpc_port for rendering engine

    # Ensure credentials and ROMs directories exist
    try:
        os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
        os.makedirs(roms_path, exist_ok=True)
        if not os.path.exists(credentials_path):
            with open(credentials_path, "w") as cred_file:
                cred_file.write("")  # Create an empty credentials file
    except Exception as e:
        logger.error(f"Error preparing credentials or ROMs directory: {e}")
        return False

    # Check if the container is already running
    if is_diambra_engine_running(container_name):
        logger.info(f"DIAMBRA Engine container '{container_name}' is already running.")
        return True

    def run_engine():
        try:
            logger.info(
                f"Starting DIAMBRA Engine container '{container_name}' with host port {host_port} mapped to container port {grpc_port}..."
            )
            result = subprocess.run(
                [
                    "docker", "run", "--rm", "-d", "--name", container_name,
                    "-v", f"{credentials_path}:/tmp/.diambra/credentials",
                    "-v", f"{roms_path}:/opt/diambraArena/roms",
                    "-p", f"{host_port}:{grpc_port}",  # Explicit port mapping
                    "docker.io/diambra/engine:latest"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0:
                logger.error(f"Error starting container '{container_name}': {result.stderr.strip()}")
                return
            logger.info(f"Container '{container_name}' started successfully with gRPC port mapped to {host_port}.")
        except Exception as e:
            logger.error(f"Unexpected error starting DIAMBRA Engine: {e}")

    # Start the Docker process in a separate thread
    engine_thread = threading.Thread(target=run_engine, daemon=True)
    engine_thread.start()

    # Wait for gRPC server readiness
    grpc_address = f"localhost:{host_port}"  # Use the mapped host port for readiness checks
    if not is_grpc_ready(address="localhost", port=host_port):
        logger.error(f"DIAMBRA Engine gRPC server '{grpc_address}' did not become ready in time.")
        return False

    logger.info(f"DIAMBRA Engine gRPC server '{grpc_address}' is ready.")
    return True
