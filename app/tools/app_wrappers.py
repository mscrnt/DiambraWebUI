# path: .app/tools/app_wrappers.py

from app.tools.utils import diambra_blueprint as Blueprint
from app.custom_wrappers.episode_settings import CharacterTester, DifficultySettings


CharacterTesterBlueprint = Blueprint(
    component_class=CharacterTester,
    component_type="wrapper",
    required=False,
    default_params={},
    arg_map={"env_index": "env_index"},
    name="Character Tester",
    description="Test each character against the current hyperparameters.",
)

DifficultySettingsBlueprint = Blueprint(
    component_class=DifficultySettings,
    component_type="wrapper",
    required=False,
    default_params={},
    arg_map={"difficulty_range": "difficulty_range", "total_timesteps": "total_timesteps", "num_envs": "num_envs"},
    name="Difficulty Settings",
    description="Incrementally adjust the difficulty of the environment.",
)



# Centralized repository for all wrapper blueprints
wrapper_blueprints = {
    "Character Tester": CharacterTesterBlueprint, 
    "Difficulty Settings": DifficultySettingsBlueprint,
}
