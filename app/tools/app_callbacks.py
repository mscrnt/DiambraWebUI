# path: .app/tools/app_callbacks.py

from stable_baselines3.common.callbacks import BaseCallback
from app.log_manager import LogManager
from app.tools.utils import diambra_blueprint as Blueprint
from diambra.arena.stable_baselines3.sb3_utils import AutoSave

# Define the AutoSave blueprint with argument mapping
AutoSaveBlueprint = Blueprint(
    component_class=AutoSave,
    component_type="callback",
    required=False,
    default_params={
        "verbose": 1,
    },
    arg_map={
        "check_freq": "autosave_freq",
        "num_envs": "num_envs",
        "save_path": "save_path",
        "filename_prefix": "filename_prefix",
        "training_manager": "training_manager",
    },
    name="AutoSave",
    description="Automatically saves the model at regular intervals and supports graceful training termination.",
)

class RenderCallback(BaseCallback):
    """
    A callback to signal the TrainingManager when the model should be updated. 
    """

    def __init__(self, training_manager, verbose=0):
        super(RenderCallback, self).__init__(verbose)
        self.training_manager = training_manager
        self.logger = LogManager("RenderCallback")

    def _on_rollout_start(self):
        """Signal TrainingManager to update the cached policy at the start of each rollout."""
        self.training_manager.set_model_updated()
        self.logger.info("Signaled TrainingManager to update cached policy.")

    def _on_step(self) -> bool:
        """Override _on_step since it is abstract in BaseCallback."""
        return True  # No specific logic required here.


# Define the RenderCallback blueprint with argument mapping
RenderCallbackBlueprint = Blueprint(
    component_class=RenderCallback,
    component_type="callback",
    required=False,
    arg_map={
        "training_manager": "training_manager",  # Pass the TrainingManager directly
    },
    name="Model Sync",
    description="Signals the TrainingManager to update cached policy during rollouts.",
)

# Centralized callback blueprint repository
callback_blueprints = {
    "AutoSave": AutoSaveBlueprint,
    "RenderCallback": RenderCallbackBlueprint,
}
