import random
import uuid  # Import uuid for unique environment IDs
import gymnasium as gym

class CharacterTester(gym.Wrapper):
    def __init__(self, env, training_stats, min_episodes_per_character=10, eval_interval=20):
        super(CharacterTester, self).__init__(env)

        # Use the provided TrainingStats instance to manage shared data
        self.training_stats = training_stats
        
        # Create a unique and persistent ID for this environment
        self.env_id = uuid.uuid4().int

        # Ensure that TrainingStats has been properly initialized
        if self.training_stats is None:
            raise ValueError("TrainingStats must be initialized before using CharacterSettings.")

        # Initialization parameters
        self.min_episodes_per_character = min_episodes_per_character
        self.eval_interval = eval_interval
        self.current_episode_rewards = 0.0
        self.current_characters = None
        self.top_pool_selection = False

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)

        # Accumulate reward for the current episode
        self.current_episode_rewards += reward

        # Check if the episode has ended
        if terminated or truncated:
            # Log or handle episode-end conditions
            print(f"Total Reward for this episode: {self.current_episode_rewards}")

        return obs, reward, terminated, truncated, info

    def reset(self, **kwargs):
        # Update stats for the characters used in the last episode
        if self.current_characters:
            print(f"Updating stats for characters: {self.current_characters} with reward: {self.current_episode_rewards}")
            self.training_stats.update_stats(self.current_characters, self.current_episode_rewards, self.env_id)  # Pass env_id here

        # Get a new set of characters for this episode
        print("Requesting new character pair for reset...")
        self.current_characters = self.training_stats.get_characters(self.env_id)  # Pass env_id to get unique characters

        # Update episode settings and reset the environment
        episode_settings = kwargs.get('options', {})
        episode_settings.update({"characters": self.current_characters})
        kwargs['options'] = episode_settings

        # Reset rewards for the new episode
        self.current_episode_rewards = 0.0

        # Display the character pair usage table after each episode
        self.training_stats.display_usage_table()

        print(f"Selected Characters for this episode: {self.current_characters}")

        return self.env.reset(**kwargs)



# Custom Wrapper to Incrementally Adjust Difficulty
class DifficultySettings(gym.Wrapper):
    def __init__(self, env, difficulty_range=(8, 8), total_timesteps=16000000, num_envs=1):
        super(DifficultySettings, self).__init__(env)
        self.difficulty_range = difficulty_range
        self.total_timesteps = total_timesteps // num_envs  # Multiply by number of environments to get effective total steps
        self.steps_per_difficulty = self.total_timesteps // (difficulty_range[1] - difficulty_range[0] + 1)
        self.total_steps = 0  # Track the total step count across all environments
        print(f"Initialized DifficultySettings with difficulty_range: {difficulty_range}, "
              f"effective_total_timesteps: {self.total_timesteps}, steps_per_difficulty: {self.steps_per_difficulty}")

    def step(self, action):
        # Increment the total step counter
        self.total_steps += 1

        # Proceed with the original step
        obs, reward, terminated, truncated, info = self.env.step(action)

        return obs, reward, terminated, truncated, info

    def reset(self, **kwargs):
        # Calculate difficulty based on total step count
        current_difficulty = min(
            self.difficulty_range[0] + (self.total_steps // self.steps_per_difficulty),
            self.difficulty_range[1]
        )
        
        # Debugging: Print how current difficulty is calculated
        print(f"Reset called. Current total step count: {self.total_steps}")
        print(f"Calculating current difficulty: "
              f"base_difficulty: {self.difficulty_range[0]}, "
              f"total_steps: {self.total_steps}, "
              f"steps_per_difficulty: {self.steps_per_difficulty}, "
              f"calculated_difficulty: {current_difficulty}")

        # Update episode settings
        episode_settings = kwargs.get('options', {})
        episode_settings.update({
            "difficulty": current_difficulty
        })

        # Print the settings for debugging purposes
        print(f"New Difficulty Settings: Difficulty: {current_difficulty}")

        # Pass the updated options to reset
        kwargs['options'] = episode_settings

        # Reset the environment and return the initial observation
        obs = self.env.reset(**kwargs)

        return obs

# Custom Wrapper for Game-Specific Settings (if needed in the future)
class GameSpecificSettings(gym.Wrapper):
    def __init__(self, env, game_id):
        super(GameSpecificSettings, self).__init__(env)
        self.game_id = game_id

    def reset(self, **kwargs):
        # Update episode settings
        episode_settings = kwargs.get('options', {})
        episode_settings.update({
            "game_id": self.game_id
        })

        # Print the settings for debugging purposes
        print(f"New Game Specific Settings: Game ID: {self.game_id}")

        # Pass the updated options to reset
        kwargs['options'] = episode_settings
        return self.env.reset(**kwargs)

    def step(self, action):
        return self.env.step(action)

