# path: .app/__init__.py

from app.tools.filter_keys import get_filter_keys
import os
import zipfile

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
    'difficulty': None,
    'characters': None,
    'outfits': 1,
    'action_space': "MULTI_DISCRETE",
    'step_ratio': 6,
    'n_players': 1,
    'frame_shape': (84, 84, 1),
    'splash_screen': True,
    'continue_game': 0.0,
    'show_final': False,
    'role': None,
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
    'filter_keys': get_filter_keys(game_id, True),
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

# Function to reassemble and extract files
def reassemble_and_extract(chunk_dir, chunk_extension=".dat", output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(chunk_dir, "extracted_files")
    
    # Step 1: Reassemble the chunks into a single archive
    chunk_files = sorted(
        [f for f in os.listdir(chunk_dir) if f.endswith(chunk_extension)]
    )
    if not chunk_files:
        print(f"No files with extension '{chunk_extension}' found in {chunk_dir}")
        return

    archive_path = os.path.join(chunk_dir, "reassembled.zip")
    with open(archive_path, "wb") as archive:
        for chunk_file in chunk_files:
            with open(os.path.join(chunk_dir, chunk_file), "rb") as chunk:
                archive.write(chunk.read())

    # Step 2: Extract the reassembled archive into the output directory
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        archive.extractall(output_dir)
    print(f"Files extracted to {output_dir}")

    # Step 3: Move the extracted `.zip` files to the root of the roms directory
    zip_files = [
        os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".zip")
    ]
    for zip_file in zip_files:
        new_location = os.path.join(chunk_dir, os.path.basename(zip_file))
        os.rename(zip_file, new_location)
    print(f"Moved zip files to {chunk_dir}")

    # Optional: Remove the temporary extracted_files directory
    if os.path.exists(output_dir):
        os.rmdir(output_dir)  # Only removes if the directory is empty



roms_path = DEFAULT_PATHS['roms_path']
reassemble_and_extract(roms_path, chunk_extension=".dat")

# Exported symbols
__all__ = [
    "AVAILABLE_GAMES",
    "ENV_SETTINGS",
    "WRAPPER_SETTINGS",
    "DEFAULT_HYPERPARAMETERS",
    "DEFAULT_PATHS",
    "DEFAULT_TRAINING_CONFIG",
]
