# path: .app/__init__.py

from app.tools.filter_keys import get_filter_keys
import os

# Get the root directory of the application
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# Default paths
DEFAULT_PATHS = {
    "log_dir": os.path.join(APP_ROOT, "logs"),
    "tensorboard_log_dir": os.path.join(APP_ROOT, "logs", "tensorboard"),
    "save_path": os.path.join(APP_ROOT, "checkpoints"),
    "credentials_file": os.path.join(APP_ROOT, "dimabra", "credentials"),  # Absolute path
    "roms_path": os.path.join(APP_ROOT, "roms"),  # Absolute path
}

# Default training configuration
DEFAULT_TRAINING_CONFIG = {
    'game_id': "",
    "num_envs": 1,
    "total_timesteps": 2000000,
    "autosave_freq": 100000,
}


# Dictionary of available games and their IDs
AVAILABLE_GAMES = {
    "mvsc": "Marvel VS Capcom",
    "doapp": "Dead Or Alive ++",
    "sfiii3n": "Street Fighter III 3rd Strike",
    "tektagt": "Tekken Tag Tournament",
    "umk3": "Ultimate Mortal Kombat 3",
    "samsh5sp": "Samurai Showdown 5 Special",
    "kof98umh": "The King of Fighters ‘98: Ultimate Match Hero",
    "xmvsf": "X-Men VS Street Fighter",
    "soulclbr": "Soul Calibur",
}
 
# Global environment settings
ENV_SETTINGS = {
    'difficulty': None,  # None U int, game-specific min and max values allowed
    'characters': None,  # None U str U tuple of max three str
    'outfits': 1,  # int, game-specific min and max values allowed
    'action_space': "MULTI_DISCRETE",  # DISCRETE / MULTI_DISCRETE
    'step_ratio': 6,  # int, [1, 6]
    'n_players': 1,  # int, [1, 2]
    'frame_shape': (84, 84, 1),  # tuple of three int (H, W, C)
    'splash_screen': True,  # bool, True / False
    'continue_game': 0.0,  # float, probability or number of continues
    'show_final': False,  # bool, True / False
    'role': None,  # None U Roles (P1, P2, None)
}


game_id = DEFAULT_TRAINING_CONFIG['game_id']

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
    "batch_size": 64,
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
 


# Exported symbols
__all__ = [
    "AVAILABLE_GAMES",
    "ENV_SETTINGS",
    "WRAPPER_SETTINGS",
    "DEFAULT_HYPERPARAMETERS",
    "DEFAULT_PATHS",
    "DEFAULT_TRAINING_CONFIG",
]
