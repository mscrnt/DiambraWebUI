# path: .app/training_script.py

import json
import sys
from diambra.arena.stable_baselines3.make_sb3_env import make_sb3_env, EnvironmentSettings, WrappersSettings
from diambra.arena import SpaceTypes, load_settings_flat_dict
from stable_baselines3 import PPO
from diambra.arena.stable_baselines3.sb3_utils import linear_schedule, AutoSave


def validate_and_convert(env_settings, wrapper_settings, hyperparameters):
    """Validate and convert settings to their correct types and ranges."""
    env_types_and_defaults = {
        "frame_shape": {"type": tuple, "default": (0, 0, 0)},
        # Skip validation of `action_space`
        "n_players": {"type": int, "range": [1, 2]},
        "step_ratio": {"type": int, "range": [1, 6]},
        "splash_screen": {"type": bool, "default": True},
        "difficulty": {"type": int, "default": None},
        "continue_game": {"type": float, "range": [0.0, 1.0]},
        "show_final": {"type": bool, "default": False},
        # Handle `role` conversion from str to int or None
        "role": {"type": (int, type(None)), "allowed": {"P1": 0, "P2": 1, "None": None}, "default": None},
        "characters": {"type": (str, tuple), "default": None},
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
        "seed": {"type": int, "default": None},  # Ensure seed is an integer
        "device": {"type": (str, "torch.device"), "default": "auto"},
    }

    def convert_value(key, value, rules):
        """Validate and convert a single value based on the provided rules."""
        try:
            if value is None or value == "":
                return rules.get("default")

            # Handle special conversion for `role`
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

            # Special handling for `seed`
            elif key == "seed":
                try:
                    value = int(value)
                    print(f"Converted field '{key}' to int: {value}")
                except ValueError:
                    raise ValueError(f"Invalid seed value: {value}. Seed must be an integer.")

            # General type validation and conversion
            else:
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

    # Validate and convert all other fields except action_space
    for key, rules in env_types_and_defaults.items():
        if key in env_settings and key != "action_space":  # Skip action_space validation
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




def main():
    """Main function for setting up and training the PPO agent."""
    if len(sys.argv) < 2:
        print("Usage: python training_script.py <config_file_path>")
        sys.exit(1)

    # Load configuration
    config_file_path = sys.argv[1]
    with open(config_file_path, "r") as f:
        config = json.load(f)

    training_config = config["training_config"]
    hyperparameters = config["hyperparameters"]
    wrapper_settings = config["wrapper_settings"]
    env_settings = config["env_settings"]

    # Convert action_space from string to SpaceTypes
    if "action_space" in env_settings:
        action_space_value = env_settings["action_space"]
        if isinstance(action_space_value, str):
            try:
                env_settings["action_space"] = getattr(SpaceTypes, action_space_value)
                print(f"Converted action_space to SpaceTypes: {env_settings['action_space']}")
            except AttributeError:
                raise ValueError(f"Invalid action_space value: {action_space_value}. Must be one of {list(SpaceTypes)}")

    # Validate and convert the configurations
    env_settings, wrapper_settings, hyperparameters = validate_and_convert(
        env_settings, wrapper_settings, hyperparameters
    )

    print("\nValidated and Converted Settings:")
    print(json.dumps(env_settings, indent=4))
    print(json.dumps(wrapper_settings, indent=4))
    print(json.dumps(hyperparameters, indent=4))
    env_settings_obj = load_settings_flat_dict(EnvironmentSettings, env_settings)
    wrapper_settings_obj = load_settings_flat_dict(WrappersSettings, wrapper_settings)

    # Calculate learning_rate and clip_range using linear_schedule
    learning_rate = linear_schedule(
        float(hyperparameters["learning_rate_start"]),
        float(hyperparameters["learning_rate_end"]),
    )
    clip_range = linear_schedule(
        float(hyperparameters["clip_range_start"]),
        float(hyperparameters["clip_range_end"]),
    )
    clip_range_vf = (
        linear_schedule(
            float(hyperparameters["clip_range_vf_start"]),
            float(hyperparameters["clip_range_vf_end"]),
        )
        if hyperparameters.get("clip_range_vf_start") and hyperparameters.get("clip_range_vf_end")
        else None
    )

    # Define policy kwargs for network architecture
    policy_kwargs = {
        "net_arch": [
            dict(
                pi=list(map(int, hyperparameters["pi_net"].split(","))) if hyperparameters.get("pi_net") else [64, 64],
                vf=list(map(int, hyperparameters["vf_net"].split(","))) if hyperparameters.get("vf_net") else [],
            )
        ]
    }

    # Create environment
    env, num_envs = make_sb3_env(
        training_config["game_id"],
        env_settings_obj,
        wrapper_settings_obj,
    )

    # Create PPO agent
    agent = PPO(
        "MultiInputPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=int(hyperparameters["n_steps"]),
        batch_size=int(hyperparameters["batch_size"]),
        n_epochs=int(hyperparameters["n_epochs"]),
        gamma=float(hyperparameters["gamma"]),
        gae_lambda=float(hyperparameters["gae_lambda"]),
        clip_range=clip_range,
        clip_range_vf=clip_range_vf,
        normalize_advantage=bool(hyperparameters["normalize_advantage"]),
        ent_coef=float(hyperparameters["ent_coef"]),
        vf_coef=float(hyperparameters["vf_coef"]),
        max_grad_norm=float(hyperparameters["max_grad_norm"]),
        target_kl=hyperparameters.get("target_kl"),
        tensorboard_log=training_config.get("tensorboard_log"),
        seed=hyperparameters.get("seed"),
        device=hyperparameters["device"],
        policy_kwargs=policy_kwargs,
    )

    # Train the agent
    agent.learn(
        total_timesteps=int(training_config["total_timesteps"]),
        callback=AutoSave(
            check_freq=int(training_config["autosave_freq"]),
            num_envs=num_envs,
            save_path=training_config.get("save_path", "./checkpoints"),
        ),
    )

    # Close the environment
    env.close()


if __name__ == "__main__":
    main()
