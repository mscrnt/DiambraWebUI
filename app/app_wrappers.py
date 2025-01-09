# path: ./app_wrappers.py

from utils import load_blueprints as Blueprint


EnhancedStatsWrapperBlueprint = Blueprint(
    component_class="",
    component_type="wrapper",
    required=True,
    default_params={},
    arg_map={"env_index": "env_index"},
    name="Enhanced Stats",
    description="Enhances the observation space with additional game statistics, such as coins, score, and player state."
)



# Centralized repository for all wrapper blueprints
wrapper_blueprints = {
    "EnhancedStatsWrapper": EnhancedStatsWrapperBlueprint,
}
