# path: ./render_manager.py

import torch
import threading
import time
from copy import deepcopy
import queue
import cv2
import numpy as np
import logging

# Initialize a logger specific to this module
logger = logging.getLogger(__name__)

frame_queue = queue.Queue(maxsize=50)


def clear_frame_queue():
    """
    Clears all frames from the frame queue. 
    """
    discarded_frames = 0
    while not frame_queue.empty():
        frame_queue.get_nowait()
        discarded_frames += 1
    logger.info("Frame queue cleared", discarded_frames=discarded_frames)


def render_frame_to_queue(frame):
    """
    Render a frame and place it in the frame queue.

    :param frame: The rendered frame (as a NumPy array).
    """
    try:
        if frame_queue.full():
            discarded_frame = frame_queue.get_nowait()  # Discard the oldest frame
            logger.debug("Discarded oldest frame to make room in queue.", discarded_frame=discarded_frame)
        
        frame_queue.put_nowait(frame)
        logger.debug("Frame added to queue successfully.")
    except queue.Full:
        logger.warning("Frame queue is full; skipping frame.")
    except Exception as e:
        logger.error("Rendering failed", exception=e)


def generate_frame_stream(frame_rate=120):
    """
    Generator function to stream frames as MJPEG.
    """
    interval = 1.0 / frame_rate
    while True:
        try:
            frame = frame_queue.get(timeout=1)  # Avoid indefinite blocking
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(interval)
        except queue.Empty:
            logger.debug("Frame queue is empty; waiting for new frames.")
        except Exception as e:
            logger.error("Error generating frame stream.", exception=e)


class RenderManager:
    """
    Manages rendering in a separate thread to ensure it does not block training.
    """
    def __init__(self, render_env, model, cache_update_interval=120, training_active_flag=None, model_updated_flag=None):
        if render_env is None or model is None:
            raise ValueError("Both 'render_env' and 'model' must be provided to initialize RenderManager.")

        self.render_env = render_env
        self.model = model
        self.cached_policy = None
        self.cache_update_interval = cache_update_interval
        self.done_event = threading.Event()
        self.render_thread = None
        self.obs = None
        self.training_active_flag = training_active_flag or (lambda: True)
        self.model_updated_flag = model_updated_flag or threading.Event()
        self.rendering_active = threading.Event()

        try:
            self.cached_policy = deepcopy(self.model.policy)
            logger.info("RenderManager initialized successfully with a cached policy.")
        except Exception as e:
            logger.error("Failed to initialize cached policy during RenderManager initialization.", exception=e)
            raise

    def _cache_policy(self):
        """Update the cached policy with a thread-safe copy."""
        try:
            self.cached_policy.load_state_dict(deepcopy(self.model.policy.state_dict()))
            logger.debug("Cached policy updated successfully.")
        except Exception as e:
            logger.error("Error while updating cached policy.", exception=e)

    def _render_loop(self, target_render_fps=60, logic_fps=12):
        """
        Rendering loop with separate timing for logic updates and frame rendering.
        """
        try:
            self.obs = self.render_env.reset()
            self.rendering_active.set()
            logger.info("Rendering thread started successfully.")

            render_interval = 1 / target_render_fps
            logic_interval = 1 / logic_fps

            last_render_time = time.time()
            last_logic_time = last_render_time

            last_logic_frame = self.render_env.render(mode="rgb_array")
            current_logic_frame = last_logic_frame

            while not self.done_event.is_set():
                if not self.training_active_flag():
                    logger.info("Training has stopped; ending render loop.")
                    break

                if self.model_updated_flag.is_set():
                    self._cache_policy()
                    self.model_updated_flag.clear()

                current_time = time.time()

                if current_time - last_logic_time >= logic_interval:
                    try:
                        with torch.no_grad():
                            action, _ = self.cached_policy.predict(self.obs, deterministic=True)
                        self.obs, _, done, _ = self.render_env.step(action)

                        last_logic_frame = current_logic_frame
                        current_logic_frame = self.render_env.render(mode="rgb_array")

                        if done:
                            self.obs = self.render_env.reset()
                    except Exception as e:
                        logger.error("Error during logic update.", exception=e)
                    last_logic_time = current_time

                if current_time - last_render_time >= render_interval:
                    try:
                        render_frame_to_queue(current_logic_frame)
                    except Exception as e:
                        logger.error("Error during frame rendering.", exception=e)
                    last_render_time = current_time

                time.sleep(0.001)
        except Exception as e:
            logger.error("Rendering loop failed.", exception=e)
        finally:
            self.rendering_active.clear()
            logger.info("Rendering thread stopped.")

    def start(self):
        """Start the render thread and the model caching mechanism."""
        try:
            self._cache_policy()
            self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
            self.render_thread.start()
            threading.Thread(target=self._update_policy_loop, daemon=True).start()
            logger.info("RenderManager started successfully.")
        except Exception as e:
            logger.error("Failed to start RenderManager.", exception=e)
            self.rendering_active.clear()

    def is_rendering(self):
        """Return the rendering status."""
        return self.rendering_active.is_set()

    def _update_policy_loop(self):
        """Periodically update the cached policy."""
        try:
            while not self.done_event.is_set():
                if not self.training_active_flag():
                    logger.info("Training has stopped, halting policy updates.")
                    break
                time.sleep(self.cache_update_interval)
                self._cache_policy()
        except Exception as e:
            logger.error("Error during policy update loop.", exception=e)

    def stop(self):
        """Stop the rendering thread and clear the frame queue."""
        try:
            logger.info("Stopping rendering thread.")
            self.done_event.set()
            if self.render_thread:
                self.render_thread.join()
            clear_frame_queue()
            logger.info("RenderManager stopped successfully.")
        except Exception as e:
            logger.error("Error stopping RenderManager.", exception=e)

