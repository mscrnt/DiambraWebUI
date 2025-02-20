# path: app/container_manager.py

import threading
import subprocess
import os
from app.log_manager import LogManager


class ContainerManager:
    def __init__(self, name, log_file="container_activity.log"):
        """
        Initialize the container manager.

        :param name: Unique name for this manager instance (e.g., 'training', 'rendering').
        :param log_file: Path to the file where container activity is logged.
        """
        self.name = name
        self.log_file = log_file
        self.logger = LogManager(f"ContainerManager[{name}]")
        self.container_process = None  # Holds the process for the container
        self.monitoring_thread = None
        self.monitoring_active = threading.Event()

    def _get_python_executable(self):
        """
        Get the path to the Python executable within the virtual environment.

        :return: Path to the Python executable.
        """
        # Adjust to the root directory and locate the virtual environment
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_executable = os.path.join(project_root, "venv", "Scripts", "python.exe")
        if not os.path.exists(python_executable):
            self.logger.error(f"Python executable not found at {python_executable}")
            raise FileNotFoundError(f"Python executable not found: {python_executable}")
        return python_executable


    def _get_roms_path(self):
        """
        Get the static path to the ROMs directory.

        :return: Path to the ROMs.
        """
        roms_path = os.path.join(os.getcwd(), "roms")
        if not os.path.exists(roms_path):
            self.logger.error(f"ROMs path not found at {roms_path}")
            raise FileNotFoundError(f"ROMs path not found: {roms_path}")
        return roms_path

    def _get_pickle_path(self):
        """
        Get the static path to the pickle file.

        :return: Path to the pickle file.
        """
        temp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, "training_manager_snapshot.pkl")

    def start_container(self, container_group, script_path, num_envs):
        """
        Start a new container and monitor its logs in real-time.

        :param container_group: Group of containers ('training_group' or 'render_group').
        :param script_path: Path to the script to execute in the container.
        :param num_envs: Number of environments (1 for rendering).
        """
        try:
            python_executable = self._get_python_executable()
            roms_path = self._get_roms_path()
            pickle_path = self._get_pickle_path()
            num_envs = str(num_envs) if num_envs else "1"

            # Construct the full command
            command = [
                "diambra",
                "run",
                "-s",
                num_envs,
                "--path.roms",
                roms_path,
                "--env.preallocateport",
                python_executable,
                script_path,
                pickle_path
            ]

            self.logger.info(f"Starting container for group '{container_group}' with command: {' '.join(command)}")

            # Start the container as a subprocess
            self.container_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                preexec_fn=None if os.name == "nt" else os.setsid
            )
            self.monitoring_active.set()

            # Start a thread to monitor logs
            self.monitoring_thread = threading.Thread(
                target=self._monitor_logs,
                args=(container_group,),
                daemon=True
            )
            self.monitoring_thread.start()

            self.logger.info(f"Container for group '{container_group}' started successfully.")
        except Exception as e:
            self.logger.error(f"Error starting container for group '{container_group}': {e}", exc_info=True)
            self.stop_container(container_group)

    def _monitor_logs(self, container_group):
        """
        Monitor the logs of the running container process.
        """
        if container_group == "render_group":
            self.logger.info(f"Skipping log monitoring for group: {container_group}.")
            return  # Skip monitoring logs for the render group

        self.logger.info(f"Monitoring logs for group: {container_group}.")
        try:
            for line in self.container_process.stdout:
                if self.monitoring_active.is_set() and line.strip():
                    try:
                        self.logger.info(f"[{container_group}] {line.strip()}")
                    except UnicodeDecodeError as e:
                        self.logger.error(f"Error decoding log line for '{container_group}': {e}")
                elif not self.monitoring_active.is_set():
                    break
        except Exception as e:
            self.logger.error(f"Error while monitoring logs for group '{container_group}': {e}", exc_info=True)
        finally:
            self.container_process.wait()
            if self.container_process.returncode != 0:
                self.logger.error(
                    f"Container for group '{container_group}' exited with return code {self.container_process.returncode}."
                )

    def stop_container(self, container_group):
        """
        Stop the running container and terminate log monitoring using 'diambra arena down'.

        :param container_group: Group of containers to stop.
        """
        try:
            self.logger.info(f"Stopping container for group: {container_group}")
            self.monitoring_active.clear()

            # Use 'diambra arena down' to gracefully stop the container group
            try:
                subprocess.run(
                    ["diambra", "arena", "down"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                self.logger.info(f"'diambra arena down' executed successfully for group: {container_group}")
            except subprocess.CalledProcessError as e:
                self.logger.error(
                    f"Failed to stop container group '{container_group}' using 'diambra arena down': {e.stderr}"
                )

            # Ensure the container process is terminated
            if self.container_process and self.container_process.poll() is None:
                self.container_process.terminate()
                self.container_process.wait()
                self.logger.info(f"Process for group '{container_group}' terminated successfully.")

        except Exception as e:
            self.logger.error(f"Failed to stop container for group '{container_group}': {e}", exc_info=True)
        finally:
            self.container_process = None
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)

    def is_monitoring(self):
        """
        Check if monitoring is active.

        :return: True if monitoring is active, False otherwise.
        """
        return self.monitoring_active.is_set()
