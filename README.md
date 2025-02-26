# Diambra WebUI

Diambra WebUI is a Reinforcement Learning (RL) framework designed to train RL agents in dynamic gaming environments. It integrates **Stable Baselines3**, custom wrappers and callbacks, and a **Flask-based WebUI** for streamlined management, visualization, and interaction.

---

## Table of Contents

- [Diambra WebUI](#diambra-webui)
  - [Table of Contents](#table-of-contents)
  - [Folder Structure](#folder-structure)
  - [Features](#features)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Steps](#steps)
  - [Usage](#usage)
    - [Training](#training)
    - [Evaluation](#evaluation)
  - [Components](#components)
    - [Core Scripts](#core-scripts)
    - [Wrappers](#wrappers)
    - [Callbacks](#callbacks)
    - [GUI](#gui)
  - [Contributing](#contributing)
  - [License](#license)

---

## Folder Structure

```
DiambraWebUI/
├── checkpoints/                # Saved models during training
├── configs/                    # Training configuration files
├── gui/                        # GUI-related Python files
├── logs/                       # Training and debugging logs
├── routes/                     # Flask blueprints for modular routes
│   ├── config_routes.py        # Config management endpoints
│   ├── dashboard_routes.py     # Main dashboard routes
│   ├── stream_routes.py        # Real-time streaming of logs or gameplay
│   ├── tensorboard_routes.py   # TensorBoard integration
│   └── training_routes.py      # Training session management
├── static/                     # Static frontend assets
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript files
│   ├── json/                   # Data files for the dashboard
│   ├── webfonts/               # Font assets
│   └── favicon.ico             # Site icon
├── templates/                  # HTML templates for Flask
│   ├── base.html               # Base layout for the app
│   ├── index.html              # Main dashboard page
│   └── tensorboard.html        # TensorBoard page
├── tools/                      # Utility scripts for RL and training
│   ├── utils.py                # General-purpose utility functions
│   ├── monitor.py              # Environment monitoring utilities
│   ├── filter_keys.py          # Key filtering for training
│   └── characters.py           # Character and environment management
├── app_callbacks.py            # RL training callbacks
├── app_wrappers.py             # RL environment wrappers
├── app.py                      # Flask app entry point
├── global_state.py             # Centralized global state management
├── log_manager.py              # Logging utility for unified logging
├── preprocessing.py            # Observation preprocessing utilities
├── README.md                   # Project documentation
├── render_manager.py           # Game frame rendering utilities
├── requirements.txt            # Python dependencies
├── train.py                    # Main training script
└── setup.py                    # Project setup and packaging
```

---

## Features

- **Dynamic Wrappers & Callbacks**: Customizable, modular environment management.
- **Flask WebUI**: Interactive control panel for managing training and monitoring progress.
- **TensorBoard Integration**: Live training metrics visualization.
- **Advanced Logging**: Comprehensive logging with real-time updates.
- **Configurable Workflows**: Save, load, and modify training configurations.
- **Hyperparameter Optimization**: Use Optuna for fine-tuning.
- **Real-time Gameplay Streaming**: Watch RL agents perform live.
- **Extensible Design**: Easy integration of new models, wrappers, and features.

---

## Installation

### Prerequisites

- Python 3.8+
- Virtual environment support (e.g., `venv` or `conda`)
- GPU with CUDA support (optional, for accelerated training)

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/mscrnt/DiambraWebUI && cd DiambraWebUI
   ```

2. **Set Up the Environment**:  
Enter each command one at a time in your terminal:

  ```bash
  python -m venv venv
  ```

  Then activate the virtual environment:
  
  ```bash
  source venv/bin/activate  # For Windows use: venv\Scripts\activate
  ```
  
  Finally, install the required packages:
  
  ```bash
  pip install -r requirements.txt
  ```

3. **Run the WebUI**:
   ```bash
   cd app && flask run --host=0.0.0.0 --port=5000 --debug
   ```

4. **Access the Interface**:
   Open `http://127.0.0.1:5000` in a web browser.

---

## Usage

### Training

- Launch the WebUI, configure training parameters, and start sessions.
- Monitor progress via live metrics, logs, and gameplay streams.

### Evaluation

- Evaluate trained models:
  ```bash
  python eval.py --model checkpoints/model.zip
  ```



## Components

### Core Scripts

1. **`train.py`**: Main training logic.
2. **`eval.py`**: Model evaluation.
4. **`log_manager.py`**: Centralized logging across components.

### Wrappers

- Located in `app_wrappers.py`.
- Enhance and modify environments, e.g., reward shaping, observation filtering.

### Callbacks

- Found in `app_callbacks.py`.
- Automate tasks such as checkpoint saving, rendering, and custom metrics.

### GUI

- **Frontend**: HTML, CSS, and JavaScript in `templates/` and `static/`.
- **Backend**: Flask route blueprints in `routes/`.

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add feature"`.
4. Push: `git push origin feature-name`.
5. Submit a pull request.

---

## License

Licensed under the MIT License.
