# path: .app/training_script.py

import json
import sys
from diambra.arena.stable_baselines3.make_sb3_env import make_sb3_env, EnvironmentSettings, WrappersSettings
from diambra.arena import SpaceTypes, load_settings_flat_dict
from stable_baselines3 import PPO
from diambra.arena.stable_baselines3.sb3_utils import linear_schedule
from stable_baselines3.common.callbacks import CallbackList
import os
import pickle
import signal

# Add the project root directory and the `app` directory to `sys.path`
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(1, os.path.join(project_root, "app"))

from app.tools.utils import dynamic_load_blueprints, initialize_callbacks, apply_wrappers
from app.log_manager import LogManager
from app import DEFAULT_PATHS


def validate_and_convert(env_settings, wrapper_settings, hyperparameters):
    """Validate and convert settings to their correct types and ranges."""
    env_types_and_defaults = {
        "frame_shape": {"type": tuple, "default": (0, 0, 0)},
        "n_players": {"type": int, "range": [1, 2]},
        "step_ratio": {"type": int, "range": [1, 6]},
        "splash_screen": {"type": bool, "default": True},
        "difficulty": {"type": int, "default": None},
        "continue_game": {"type": float, "range": [0.0, 1.0]},
        "show_final": {"type": bool, "default": False},
        "role": {"type": (int, type(None)), "allowed": {"P1": 0, "P2": 1, "None": None}, "default": None},
        "characters": {
            "type": (str, tuple),
            "default": None,
            "allowed": [
                "Chun-Li", "Ryu", "Zangief", "Morrigan", "Captain Commando", "Megaman", "Strider Hiryu",
                "Spider Man", "Jin", "Captain America", "Venom", "Hulk", "Gambit", "War Machine", "Wolverine",
                "Roll", "Onslaught", "Alt-Venom", "Alt-Hulk", "Alt-War Machine", "Shadow Lady", "Alt-Morrigan",
                None
            ],
        },
        "outfits": {"type": int, "default": 1},
    }

    wrapper_types_and_defaults = {
        "stack_frames": {"type": int, "range": [1, 48]},
        "dilation": {"type": int, "range": [1, 48]},
        "no_attack_buttons_combinations": {"type": bool, "default": False},
        "normalize_reward": {"type": bool, "default": False},
        "normalization_factor": {"type": float, "default": 0.5},
        "stack_actions": {"type": int, "range": [1, 48]},
        "scale": {"type": bool, "default": False},
        "exclude_image_scaling": {"type": bool, "default": False},
        "flatten": {"type": bool, "default": False},
        "process_discrete_binary": {"type": bool, "default": False},
        "role_relative": {"type": bool, "default": False},
        "add_last_action": {"type": bool, "default": False},
        "filter_keys": {"type": list, "default": []},
    }

    ppo_parameter_types = {
        "learning_rate": {"type": (float, callable), "default": 3e-4},
        "n_steps": {"type": int, "range": [2, None]},
        "batch_size": {"type": int, "range": [1, None]},
        "n_epochs": {"type": int, "range": [1, None]},
        "gamma": {"type": float, "range": [0.0, 1.0]},
        "gae_lambda": {"type": float, "range": [0.0, 1.0]},
        "clip_range": {"type": (float, callable), "default": 0.2},
        "clip_range_vf": {"type": (type(None), float, callable), "default": None},
        "normalize_advantage": {"type": bool, "default": False},
        "ent_coef": {"type": float, "range": [0.0, None]},
        "vf_coef": {"type": float, "range": [0.0, None]},
        "max_grad_norm": {"type": float, "range": [0.0, None]},
        "use_sde": {"type": bool, "default": False},
        "sde_sample_freq": {"type": int, "range": [-1, None]},
        "target_kl": {"type": (type(None), float), "default": None},
        "stats_window_size": {"type": int, "range": [1, None]},
        "tensorboard_log": {"type": (str, None), "default": None},
        "policy_kwargs": {"type": (dict, None), "default": None},
        "verbose": {"type": int, "range": [0, 2]},
        "seed": {"type": int, "default": None},
        "device": {"type": (str, "torch.device"), "default": "auto"},
    }

    def convert_value(key, value, rules):
        """Validate and convert a single value based on the provided rules."""
        try:
            if value is None or value == "":
                return rules.get("default")

            # Special handling for `characters`
            if key == "characters":
                if isinstance(value, str):
                    if "," in value:
                        value = tuple(map(str.strip, value.split(",")))
                        print(f"Converted 'characters' field to tuple: {value}")
                    else:
                        value = value.strip()
                if isinstance(value, tuple):
                    if len(value) > 3:
                        raise ValueError(f"'characters' tuple cannot have more than 3 elements: {value}")
                    for character in value:
                        if character not in rules["allowed"]:
                            raise ValueError(f"Invalid character '{character}' in 'characters'. Allowed: {rules['allowed']}")
                elif isinstance(value, str) and value not in rules["allowed"]:
                    raise ValueError(f"Invalid character '{value}' in 'characters'. Allowed: {rules['allowed']}")
                return value

            # Handle `role` conversion
            if key == "role":
                allowed_roles = rules["allowed"]
                if value not in allowed_roles:
                    raise ValueError(f"Invalid role: {value}. Allowed values: {list(allowed_roles.keys())}")
                value = allowed_roles[value]
                print(f"Converted field '{key}' to {value}")

            # Convert string booleans to actual booleans
            elif rules["type"] == bool and isinstance(value, str):
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                else:
                    raise ValueError(f"Invalid boolean string for '{key}': {value}")
                print(f"Converted field '{key}' to bool: {value}")

            # Special handling for `frame_shape`
            elif key == "frame_shape" and isinstance(value, str):
                try:
                    value = tuple(map(int, value.replace(" ", "").split(",")))
                    print(f"Converted field '{key}' to tuple: {value}")
                except ValueError as e:
                    raise ValueError(f"Invalid format for 'frame_shape'. Expected 'H,W,C', got: '{value}'. Error: {e}")

            # General type validation and conversion
            allowed_types = rules["type"] if isinstance(rules["type"], tuple) else (rules["type"],)
            if not isinstance(value, allowed_types):
                if float in allowed_types or int in allowed_types:
                    value = float(value) if "." in str(value) else int(value)
                else:
                    raise TypeError(f"Invalid type for '{key}': {value} (expected {allowed_types}).")
            print(f"Converted field '{key}' to {type(value).__name__}: {value}")

            # Range validation
            if "range" in rules:
                min_val, max_val = rules["range"]
                if (min_val is not None and value < min_val) or (max_val is not None and value > max_val):
                    raise ValueError(f"Value for '{key}' is out of range: {value}.")

            return value
        except Exception as e:
            print(f"Error converting field '{key}' with value '{value}': {e}")
            raise

    # Validate and convert all fields except action_space
    for key, rules in env_types_and_defaults.items():
        if key in env_settings and key != "action_space":
            print(f"Checking env_settings[{key}]: {env_settings[key]}")
            env_settings[key] = convert_value(key, env_settings[key], rules)

    for key, rules in wrapper_types_and_defaults.items():
        if key in wrapper_settings:
            print(f"Checking wrapper_settings[{key}]: {wrapper_settings[key]}")
            wrapper_settings[key] = convert_value(key, wrapper_settings[key], rules)

    for key, rules in ppo_parameter_types.items():
        if key in hyperparameters:
            print(f"Checking hyperparameters[{key}]: {hyperparameters[key]}")
            hyperparameters[key] = convert_value(key, hyperparameters[key], rules)

    return env_settings, wrapper_settings, hyperparameters

def validate_and_initialize_blueprints(training_manager):
    """
    Validate and initialize dynamically loaded blueprints for callbacks and wrappers.
    """
    training_manager.wrapper_blueprints = dynamic_load_blueprints("app.tools.app_wrappers")
    training_manager.callback_blueprints = dynamic_load_blueprints("app.tools.app_callbacks")

    logger = LogManager("validate_and_initialize_blueprints")
    logger.info("Validating and initializing blueprints...")

    # Print loaded blueprints for debugging
    logger.info(f"Loaded Wrapper Blueprints: {list(training_manager.wrapper_blueprints.keys())}")
    logger.info(f"Loaded Callback Blueprints: {list(training_manager.callback_blueprints.keys())}")

    initialize_callbacks(training_manager)
    logger.info("Blueprint validation and initialization completed.")


def validate_loaded_config(training_manager):
    """
    Validate and clean the configuration after loading from the pickle file.
    """
    try:
        config = training_manager.active_config["config"]
        env_settings = config["env_settings"]
        wrapper_settings = config["wrapper_settings"]
        hyperparameters = config["hyperparameters"]

        print("Validating and converting configuration...")
        env_settings, wrapper_settings, hyperparameters = validate_and_convert(env_settings, wrapper_settings, hyperparameters)

        config["env_settings"] = env_settings
        config["wrapper_settings"] = wrapper_settings
        config["hyperparameters"] = hyperparameters
        training_manager.active_config["config"] = config
        print("Configuration validated and updated successfully.")
    except Exception as e:
        print(f"Error validating configuration: {e}")
        raise RuntimeError("Failed to validate loaded configuration.") from e


def load_from_pickle(file_path):
    """Load an object from a pickle file."""
    try:
        with open(file_path, "rb") as f:
            obj = pickle.load(f)
        print(f"Object loaded from pickle file: {file_path}")
        return obj
    except Exception as e:
        print(f"Failed to load object from {file_path}: {e}")
        raise RuntimeError(f"Failed to load object from {file_path}: {e}")

def signal_handler(signum, frame):
    """Handles termination signals (e.g., SIGTERM, SIGINT)."""
    global agent, env, save_path
    print(f"\nReceived termination signal: {signum}. Cleaning up...")
    if agent and save_path:
        model_path = os.path.join(save_path, "last_model.zip")
        print(f"Saving the model to: {model_path}")
        agent.save(model_path)
    print("Cleanup complete. Exiting.")
    sys.exit(0)

def main():
    """Main function for setting up and training the PPO agent."""
    global agent, env, save_path

    # Register signal handlers for SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if len(sys.argv) < 2:
        print("Usage: python training_script.py <pickle_file_path>")
        sys.exit(1)

    pickle_file_path = sys.argv[1]
    training_manager = load_from_pickle(pickle_file_path)

    # Validate and initialize configuration and blueprints
    if not training_manager or not training_manager.active_config or not training_manager.active_config["use_active"]:
        print("No valid active configuration found in the loaded TrainingManager.")
        sys.exit(1)

    validate_loaded_config(training_manager)
    validate_and_initialize_blueprints(training_manager)

    # Extract configurations
    training_config = training_manager.active_config["config"]["training_config"]
    hyperparameters = training_manager.active_config["config"]["hyperparameters"]
    wrapper_settings = training_manager.active_config["config"]["wrapper_settings"]
    env_settings = training_manager.active_config["config"]["env_settings"]
    callback_instances = training_manager.callback_instances

    # Log the active configuration for debugging
    print("Active Configuration:")
    print(json.dumps(training_manager.active_config, indent=4))

    # Ensure the TensorBoard log path and save path are set
    save_path = training_config.get("save_path", DEFAULT_PATHS["save_path"])
    os.makedirs(save_path, exist_ok=True)
    print(f"Model checkpoints will be saved to: {save_path}")

    tensorboard_log_dir = training_config.get("tensorboard_log", DEFAULT_PATHS["tensorboard_log_dir"])
    os.makedirs(tensorboard_log_dir, exist_ok=True)
    print(f"TensorBoard logs will be saved to: {tensorboard_log_dir}")

    # Log the loaded callbacks for debugging
    print(f"Loaded callbacks: {[type(cb).__name__ for cb in callback_instances]}")

    # Convert `action_space` to SpaceTypes
    if "action_space" in env_settings:
        action_space_value = env_settings["action_space"].lower()
        env_settings["action_space"] = (
            SpaceTypes.DISCRETE if action_space_value == "discrete" else SpaceTypes.MULTI_DISCRETE
        )

    # Convert settings to objects
    env_settings_obj = load_settings_flat_dict(EnvironmentSettings, env_settings)
    wrapper_settings_obj = load_settings_flat_dict(WrappersSettings, wrapper_settings)

    # Handle dynamic schedules for hyperparameters
    hyperparameters["learning_rate"] = linear_schedule(
        float(hyperparameters["learning_rate_start"]),
        float(hyperparameters["learning_rate_end"]),
    )
    hyperparameters["clip_range"] = linear_schedule(
        float(hyperparameters["clip_range_start"]),
        float(hyperparameters["clip_range_end"]),
    )
    if hyperparameters.get("clip_range_vf_start") and hyperparameters.get("clip_range_vf_end"):
        hyperparameters["clip_range_vf"] = linear_schedule(
            float(hyperparameters["clip_range_vf_start"]),
            float(hyperparameters["clip_range_vf_end"]),
        )

    policy_kwargs = {
        "net_arch": [
            dict(
                pi=list(map(int, hyperparameters["pi_net"].split(","))) if hyperparameters.get("pi_net") else [64, 64],
                vf=list(map(int, hyperparameters["vf_net"].split(","))) if hyperparameters.get("vf_net") else [],
            )
        ]
    }
    hyperparameters["policy_kwargs"] = policy_kwargs

    # Initialize the environment
    print("Initializing environment...")
    env, num_envs = make_sb3_env(
        training_config["game_id"],
        env_settings_obj,
        wrapper_settings_obj,
    )

    # Train with callbacks
    print("Creating PPO agent...")
    agent = PPO(
        "MultiInputPolicy",
        env,
        verbose=1,
        learning_rate=hyperparameters["learning_rate"],
        n_steps=hyperparameters["n_steps"],
        batch_size=hyperparameters["batch_size"],
        n_epochs=hyperparameters["n_epochs"],
        gamma=hyperparameters["gamma"],
        gae_lambda=hyperparameters["gae_lambda"],
        clip_range=hyperparameters["clip_range"],
        tensorboard_log=tensorboard_log_dir,
        seed=hyperparameters.get("seed"),
        device=hyperparameters["device"],
    )

    # Log the CallbackList for debugging
    callback_list = CallbackList(callback_instances)
    print(f"CallbackList contains: {[type(cb).__name__ for cb in callback_list.callbacks]}")

    print("Starting training...")
    try:
        agent.learn(total_timesteps=int(training_config["total_timesteps"]), callback=callback_list)
    except KeyboardInterrupt:
        print("\nraining interrupted by user.")
    except Exception as e:
        print(f"")
    finally:
        print("Saving the model before exiting...")
        try:
            agent.save(os.path.join(save_path, "last_model.zip"))
            print(f"Model saved to: {os.path.join(save_path, 'last_model.zip')}")
        except Exception as e:
            print(f"Failed to save model: {e}")
        if env:
            print("Closing the environment...")
            try:
                print("Environment closed.")
            except Exception as e:
                print(f"Failed to close environment: {e}")
    print("Training complete. Exiting.")
    print("Please ignore the 'No such container' error messages...")

    try:
        env.close()
    except Exception as e:
        print(f"")

if __name__ == "__main__":
    main()