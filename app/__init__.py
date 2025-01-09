# path: gui/__init__.py

from app.tools.filter_keys import get_filter_keys

# Game Settings
ENV_SETTINGS = {
    'game_id': "",
    'difficulty': 1,
    'characters': (""), 
    'action_space': "",
    'step_ratio': 1,
    'frame_shape': (84, 84, 1)
}

game_id = ENV_SETTINGS['game_id']

# Wrappers Settings
WRAPPER_SETTINGS = {
    'wrappers': [],
    'stack_frames': 4,
    'dilation': 1,
    'no_attack_buttons_combinations': False,
    'normalize_reward': True,
    'normalization_factor': 1.0,
    'stack_actions': 4,
    'scale': True,
    'exclude_image_scaling': True,
    'flatten': True,
    'process_discrete_binary': True,
    'role_relative': True,
    'add_last_action': True,
    'filter_keys': get_filter_keys(game_id, True)
}

# Default hyperparameters
DEFAULT_HYPERPARAMETERS = {
    "n_steps": 256,
    "batch_size": 256,
    "gamma": 0.94,
    "gae_lambda": 0.95,
    "clip_range_start": 0.15,
    "clip_range_end": 0.025,
    "learning_rate_start": 0.00025,
    "learning_rate_end": 0.0000025,
    "n_epochs": 4,
    "vf_coef": 0.9,
    "ent_coef": 0.01,
    "max_grad_norm": 0.5,
    "normalize_advantage": True,
    "seed": 42,
    "device": "auto", 
    "pi_net": "64,64",  
    "vf_net": None,
    "clip_range_vf_start": None,
    "clip_range_vf_end": None,
    "target_kl": None,
}
 
# Default paths
DEFAULT_PATHS = {
    "log_dir": "./logs",
    "tensorboard_log_dir": "./logs/tensorboard",
    "save_path": "./checkpoints",
    "dimabra_path": "./dimabra",
}

# Default training configuration
DEFAULT_TRAINING_CONFIG = {
    "num_envs": 1,
    "total_timesteps": 2000000,
    "autosave_freq": 100000,
}



# Exported symbols
__all__ = ["DEFAULT_TRAINING_CONFIG", "DEFAULT_HYPERPARAMETERS", "DEFAULT_PATHS", "DB_CONFIG", "ENV_SETTINGS", "WRAPPER_SETTINGS"]
