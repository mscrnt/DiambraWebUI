# path: global_state.py
from app.training_manager import TrainingManager
from app.log_manager import LogManager

# Global instance of TrainingManager
training_manager = TrainingManager()

# Global instance of LogManager
app_logger = LogManager("global")

# Hook for application exit to close the DB pool gracefully
import atexit
