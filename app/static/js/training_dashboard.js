//path: /static/js/training_dashboard.js

let tooltips = {};

// Utility function for element selection with error handling
function getElement(selector, isId = true) {
    const element = isId ? document.getElementById(selector) : document.querySelector(selector);
    if (!element) console.error(`Element not found: ${selector}`);
    return element;
}

// Utility function for fetching data
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch data from ${url}:`, error);
        return null;
    }
}

// Fetch the tooltips.json dynamically
async function fetchTooltips() {
    try {
        const response = await fetch("/static/json/tooltips.json");
        Object.assign(tooltips, await response.json());
        console.log("Tooltips loaded successfully.");
    } catch (error) {
        console.error("Failed to fetch tooltips:", error);
    }
}

// Open the tooltip modal
function openModal(key) {
    const modal = document.getElementById("tooltip-modal");
    if (!modal) {
        console.error("Tooltip modal not found in the DOM.");
        return;
    }

    const titleElement = modal.querySelector("#modal-title");
    const descriptionElement = modal.querySelector("#modal-description");
    const exampleElement = modal.querySelector("#modal-example");
    const proTipElement = modal.querySelector("#modal-pro-tip");

    if (!titleElement || !descriptionElement || !exampleElement || !proTipElement) {
        console.error("Modal elements are missing in the DOM.");
        return;
    }

    const tooltip = tooltips[key];
    if (tooltip) {
        titleElement.innerText = tooltip.title || key.replace("_", " ").toUpperCase();
        descriptionElement.innerText = tooltip.description || "No description available.";
        exampleElement.innerText = tooltip.example || "No example available.";
        proTipElement.innerText = tooltip.proTip || "No pro tip available.";
    } else {
        console.warn(`Tooltip for key "${key}" not found.`);
        titleElement.innerText = key.replace("_", " ").toUpperCase();
        descriptionElement.innerText = "No details available.";
        exampleElement.innerText = "";
        proTipElement.innerText = "";
    }
    modal.style.display = "block";
}

// Close the tooltip modal
function closeModal() {
    const modal = document.getElementById("tooltip-modal");
    if (modal) modal.style.display = "none";
}

// Initialize tooltips and attach event listeners
async function initializeTooltips() {
    await fetchTooltips();

    document.querySelectorAll(".tooltip-icon").forEach((icon) => {
        const key = icon.getAttribute("data-tooltip-key");
        if (key) {
            icon.addEventListener("click", () => openModal(key));
        }
    });

    console.log("Tooltips initialized.");
}

function initializeConfigManager() {
    let isUnsaved = false;

    // Utility function to update options in a dropdown
    function populateDropdown(selectElement, options, defaultOption = { value: "default", text: "Default" }) {
        selectElement.innerHTML = `<option value="${defaultOption.value}">${defaultOption.text}</option>`;
        options.forEach(option => {
            const opt = document.createElement("option");
            opt.value = option;
            opt.textContent = option;
            selectElement.appendChild(opt);
        });
    }

    // Utility function to populate inputs
    function populateInputs(config, section, selectorPrefix) {
        Object.entries(config[section] || {}).forEach(([key, value]) => {
            const input = getElement(`[name="${selectorPrefix}[${key}]"]`, false);
            if (input) {
                input.value = input.type === "number" && value !== undefined ? parseFloat(value) : value || "";
            }
        });
    }

    // Fetch and populate configurations
    async function fetchConfigs() {
        const configSelect = getElement("config-select");
        const data = await fetchData("/config/list_configs");
        if (data && data.configs) {
            populateDropdown(configSelect, data.configs);
            console.log("Configurations fetched and populated.");
        }
    }

    // Mark the configuration as unsaved
    function markUnsaved() {
        const configSelect = getElement("config-select");
        if (isUnsaved) return;

        const currentConfig = configSelect.value;
        const unsavedOption = document.createElement("option");
        unsavedOption.value = currentConfig.includes("~unsaved~")
            ? currentConfig
            : `${currentConfig} ~unsaved~`;
        unsavedOption.textContent = unsavedOption.value;
        configSelect.appendChild(unsavedOption);
        configSelect.value = unsavedOption.value;
        isUnsaved = true;
    }

    // Load a configuration (default or selected)
    async function loadConfig(configName) {
        const endpoint = configName === "default" ? "/config/load_default_config" : `/config/load_config/${configName}`;
        const data = await fetchData(endpoint);

        if (data && data.config) {
            populateInputs(data.config, "training_config", "training_config");
            populateInputs(data.config, "hyperparameters", "hyperparameters");

            document.querySelectorAll(".wrapper-checkbox").forEach(checkbox => {
                checkbox.checked = data.config.enabled_wrappers?.includes(checkbox.value) || false;
            });

            document.querySelectorAll(".callback-checkbox").forEach(checkbox => {
                checkbox.checked = data.config.enabled_callbacks?.includes(checkbox.value) || false;
            });

            console.log(`Configuration '${configName}' loaded successfully.`);
        } else {
            console.error(`Failed to load configuration '${configName}'.`);
        }
    }

    // Save the current configuration
    async function saveConfig() {
        const configSelect = getElement("config-select");
        const currentConfig = configSelect.value;

        if (currentConfig === "default") {
            alert("Cannot overwrite the Default configuration.");
            return;
        }

        const configName = currentConfig.includes("~unsaved~")
            ? currentConfig.replace(" ~unsaved~", "")
            : prompt("Enter a name for the configuration:");
        if (!configName) return;

        const data = {
            name: configName,
            overwrite: currentConfig.includes("~unsaved~"),
            config: {
                training_config: {},
                hyperparameters: {},
                wrappers: [],
                callbacks: [],
            },
        };

        document.querySelectorAll(".config-input").forEach(input => {
            const [section, key] = input.name.match(/(\w+)\[(\w+)\]/).slice(1);
            data.config[section][key] = input.value;
        });

        document.querySelectorAll(".wrapper-checkbox:checked").forEach(checkbox => {
            data.config.wrappers.push(checkbox.value);
        });

        document.querySelectorAll(".callback-checkbox:checked").forEach(checkbox => {
            data.config.callbacks.push(checkbox.value);
        });

        const response = await fetchData("/config/save_config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        if (response) {
            alert(response.message);
            await fetchConfigs();
            configSelect.value = configName;
            isUnsaved = false;
        }
    }

    // Delete the selected configuration
    async function deleteConfig() {
        const configName = getElement("config-select").value;

        if (configName === "default") {
            alert("Cannot delete the Default configuration.");
            return;
        }

        const response = await fetchData(`/config/delete_config/${configName}`, { method: "DELETE" });
        if (response) {
            alert(response.message);
            await fetchConfigs();
        }
    }

    // Add event listeners
    function addListeners() {
        getElement("load-config").onclick = () => loadConfig(getElement("config-select").value);
        getElement("save-changes").onclick = saveConfig;
        getElement("delete-config").onclick = deleteConfig;
        document.querySelectorAll(".config-input, .wrapper-checkbox, .callback-checkbox").forEach(input => {
            input.addEventListener("change", markUnsaved);
        });
    }

    // Initialize
    (async function init() {
        await fetchConfigs();
        addListeners();
        console.log("Configuration Manager initialized.");
    })();
}



// Initialize log streaming for training logs
function initializeLogStreaming() {
    const logOutput = document.getElementById("training-logs");
    if (!logOutput) {
        console.warn("Log output element not found.");
        return;
    }

    let isUserScrolling = false;

    // Detect if the user is scrolling
    logOutput.addEventListener("scroll", () => {
        const isAtBottom =
            logOutput.scrollHeight - logOutput.scrollTop === logOutput.clientHeight;
        isUserScrolling = !isAtBottom;
    });

    const eventSource = new EventSource("/stream/logs"); // Adjusted route
    eventSource.onmessage = (event) => {
        const newLogEntry = document.createElement("div");
        newLogEntry.textContent = event.data;
        logOutput.appendChild(newLogEntry);

        // Only auto-scroll if the user is not actively scrolling
        if (!isUserScrolling) {
            logOutput.scrollTop = logOutput.scrollHeight;
        }
    };

    // Allow re-enabling auto-scroll when the user scrolls back to the bottom
    const observer = new MutationObserver(() => {
        const isAtBottom =
            logOutput.scrollHeight - logOutput.scrollTop === logOutput.clientHeight;
        if (isAtBottom) {
            isUserScrolling = false; // Re-enable auto-scrolling
        }
    });

    observer.observe(logOutput, { childList: true });
}


// Initialize video feed logic with placeholder
async function initializeVideoFeed() {
    const videoPlaceholder = document.getElementById("video-placeholder");
    const videoFeed = document.getElementById("video-feed");

    if (!videoPlaceholder || !videoFeed) {
        console.error("Video elements are missing in the DOM.");
        return;
    }

    // Ensure placeholder is visible by default
    videoPlaceholder.style.display = "block";
    videoFeed.style.display = "none";

    const checkRenderStatus = async () => {
        try {
            const response = await fetch("/training/render_status"); // Adjusted route
            const { rendering } = await response.json();

            if (rendering) {
                videoPlaceholder.style.display = "none";
                videoFeed.style.display = "block";
            } else {
                setTimeout(checkRenderStatus, 1000); // Retry every second
            }
        } catch (error) {
            console.error("Error checking render status:", error);
            setTimeout(checkRenderStatus, 1000); // Retry in case of error
        }
    };

    checkRenderStatus(); // Start checking rendering status
}




function initializeBatchSizeDropdown() {
    const nStepsInput = document.querySelector(`[name="hyperparameters[n_steps]"]`);
    const numEnvsInput = document.querySelector(`[name="training_config[num_envs]"]`);
    const batchSizeSelect = document.getElementById("batch-size-select");

    if (!nStepsInput || !numEnvsInput || !batchSizeSelect) {
        console.error("Batch size, n_steps, or num_envs input is missing in the DOM.");
        return;
    }

    // Function to calculate valid batch sizes
    function calculateValidBatchSizes(nSteps, numEnvs) {
        console.log(`Calculating valid batch sizes for n_steps: ${nSteps}, num_envs: ${numEnvs}`);
        const totalRollout = nSteps * numEnvs;
        console.log(`Total rollout (n_steps * num_envs): ${totalRollout}`);

        const validBatchSizes = [];
        for (let nMinibatches = 1; nMinibatches <= totalRollout; nMinibatches++) {
            if (totalRollout % nMinibatches === 0) {
                validBatchSizes.push(totalRollout / nMinibatches);
            }
        }

        console.log(`Valid batch sizes: ${validBatchSizes}`);
        return validBatchSizes.sort((a, b) => a - b); // Sort ascending
    }

    // Function to populate the dropdown with valid batch sizes
    function populateBatchSizeDropdown() {
        const nSteps = parseInt(nStepsInput.value, 10);
        const numEnvs = parseInt(numEnvsInput.value, 10);

        console.log(`Populating batch size dropdown: n_steps=${nSteps}, num_envs=${numEnvs}`);

        if (isNaN(nSteps) || isNaN(numEnvs)) {
            console.error("Invalid n_steps or num_envs value.");
            return;
        }

        const validBatchSizes = calculateValidBatchSizes(nSteps, numEnvs);

        // Clear existing options
        batchSizeSelect.innerHTML = "";

        if (validBatchSizes.length) {
            // Populate dropdown with valid batch sizes
            validBatchSizes.forEach((size) => {
                const option = document.createElement("option");
                option.value = size;
                option.textContent = size;
                batchSizeSelect.appendChild(option);
            });

            // Select the second to highest batch size by default
            batchSizeSelect.value = validBatchSizes[validBatchSizes.length - 2];
            console.log(`Default selected batch size: ${batchSizeSelect.value}`);
        } else {
            console.warn("No valid batch sizes available for the given n_steps and num_envs.");
            const defaultOption = document.createElement("option");
            defaultOption.value = "";
            defaultOption.textContent = "No valid batch sizes available";
            defaultOption.disabled = true;
            batchSizeSelect.appendChild(defaultOption);
        }
    }

    // Attach listeners to dynamically update the dropdown
    nStepsInput.addEventListener("input", populateBatchSizeDropdown);
    numEnvsInput.addEventListener("input", populateBatchSizeDropdown);

    // Initialize batch size dropdown based on default values
    console.log("Initializing batch size dropdown...");
    populateBatchSizeDropdown();
}



// Toggle the visibility of the dropdown menu
function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
}

// Update the label of the dropdown button based on selected options
function updateFilterKeysLabel() {
    const dropdownButton = document.querySelector(".dropdown-toggle");
    if (!dropdownButton) return;

    const checkboxes = document.querySelectorAll("#filter-keys-dropdown input.filter-key-checkbox");
    const selectedCount = Array.from(checkboxes).filter((checkbox) => checkbox.checked).length;
    dropdownButton.innerHTML = `Selected (${selectedCount}) <i class="fas fa-chevron-down"></i>`;
}

// Function to toggle all filter keys
function toggleSelectAllKeys() {
    const selectAllCheckbox = document.getElementById("select-all-keys");
    const checkboxes = document.querySelectorAll("#filter-keys-dropdown input.filter-key-checkbox");

    if (!selectAllCheckbox || !checkboxes.length) return;

    // Set the checked state of all checkboxes to match the "Select All" checkbox
    checkboxes.forEach((checkbox) => {
        checkbox.checked = selectAllCheckbox.checked;
    });

    // Update the label after toggling
    updateFilterKeysLabel();
}

// Initialize the dropdown and automatically select all keys
function initializeFilterKeysDropdown() {
    const dropdown = document.getElementById("filter-keys-dropdown");
    if (!dropdown) return;

    // Automatically select all keys
    const checkboxes = dropdown.querySelectorAll("input.filter-key-checkbox");
    checkboxes.forEach((checkbox) => {
        checkbox.checked = true; // Auto-select all keys
    });

    // Update the "Select All" checkbox to reflect the state
    const selectAllCheckbox = document.getElementById("select-all-keys");
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = true; // Ensure "Select All" is also checked
    }

    // Update the dropdown label to reflect the selected count
    updateFilterKeysLabel();

    // Close dropdown if clicked outside
    document.addEventListener("click", (event) => {
        const dropdownButton = document.querySelector(".dropdown-toggle");
        if (
            dropdown.style.display === "block" &&
            !dropdown.contains(event.target) &&
            !dropdownButton.contains(event.target)
        ) {
            dropdown.style.display = "none";
        }
    });

    console.log("Filter Keys dropdown initialized.");
}


async function initializeGameSelectListener(gameId) {
    try {
        // Clear the selected characters input
        const characterInput = document.getElementById("env-setting-characters");
        if (characterInput) {
            characterInput.value = ""; // Clear the value
        }

        // Fetch the updated environment settings 
        const response = await fetch("/update_game_environment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_id: gameId }),
        });

        if (response.ok) {
            const { env_settings, filter_keys } = await response.json(); // Include filter_keys from backend
            console.log(`Environment settings updated for game: ${gameId}`, env_settings);

            // Update filter keys dropdown
            const filterKeysDropdown = document.getElementById("filter-keys-dropdown");
            if (filterKeysDropdown) {
                console.log("Updating filter keys dropdown...");
                filterKeysDropdown.innerHTML = ""; // Clear existing options

                // Add a "Select All" checkbox
                const selectAllOption = document.createElement("div");
                selectAllOption.className = "dropdown-item";
                selectAllOption.innerHTML = `
                    <label style="display: flex; align-items: center; gap: 10px;">
                        <input type="checkbox" id="select-all-keys" onchange="toggleSelectAllKeys()">
                        Select All
                    </label>
                `;
                filterKeysDropdown.appendChild(selectAllOption);

                // Populate new filter keys and auto-select all
                filter_keys.forEach((key) => {
                    const option = document.createElement("div");
                    option.className = "dropdown-item";
                    option.innerHTML = `
                        <label style="display: flex; align-items: center; gap: 10px;">
                            <input type="checkbox" class="filter-key-checkbox" name="wrapper_settings[filter_keys][]" value="${key}" checked onchange="updateFilterKeysLabel()">
                            ${key}
                        </label>
                    `;
                    filterKeysDropdown.appendChild(option);
                });

                // Automatically select all keys
                const checkboxes = filterKeysDropdown.querySelectorAll("input.filter-key-checkbox");
                checkboxes.forEach((checkbox) => {
                    checkbox.checked = true;
                });

                // Set "Select All" checkbox to checked
                const selectAllCheckbox = document.getElementById("select-all-keys");
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = true;
                }

                // Update filter keys label
                updateFilterKeysLabel();
            }

            // Iterate over the remaining environment settings
            Object.entries(env_settings).forEach(([key, value]) => {
                const fieldId = `env-setting-${key}`; // Use consistent ID naming
                console.log(`Processing key: ${key}`, { fieldId, value });

                // Locate the field in the DOM
                const field = document.getElementById(fieldId);
                if (!field) {
                    console.warn(`No matching field found in DOM for key: ${key} with fieldId: ${fieldId}`);
                    return;
                }

                // Populate dropdown fields (select elements)
                if (field.tagName === "SELECT") {
                    console.log(`Populating dropdown for key: ${key}`);
                    field.innerHTML = ""; // Clear existing options

                    if (Array.isArray(value)) {
                        value.forEach((option) => {
                            const optionElement = document.createElement("option");
                            if (typeof option === "object" && option.value && option.label) {
                                optionElement.value = option.value;
                                optionElement.textContent = option.label;
                            } else {
                                optionElement.value = option;
                                optionElement.textContent = option;
                            }
                            field.appendChild(optionElement);
                        });
                    } else {
                        console.warn(`Expected an array for ${key}, but got:`, value);
                    }
                } else {
                    // Handle non-dropdown fields
                    console.log(`Setting value for key: ${key}`, { value });
                    if (field.value !== undefined) {
                        field.value = value || "";
                    } else {
                        console.warn(`Field for key ${key} does not support value assignment.`);
                    }
                }
            });
        } else {
            const error = await response.json();
            console.error("Failed to fetch environment settings:", error);
        }
    } catch (error) {
        console.error("Error updating game values:", error);
    }
}


async function initializeCharacterSelectListener() {
    const characterInput = document.getElementById("env-setting-characters");
    if (!characterInput) return;

    characterInput.addEventListener("click", async () => {
        const gameSelect = document.getElementById("game-select");
        const gameId = gameSelect.value;

        if (!gameId) {
            alert("Please select a game first.");
            return;
        }

        const response = await fetch(`/get_characters/${gameId}`);
        if (!response.ok) {
            console.error("Failed to fetch character data.");
            return;
        }

        const { gameType, characters } = await response.json();
        gameSelect.dataset.gameType = gameType; // Store the gameType in a data attribute
        openCharacterModal(gameType, characters);
        toggleCharacterModal(true); // Open the modal

    });
}

function openCharacterModal(gameType, characters) {
    const modal = document.getElementById("character-modal");
    const characterList = document.getElementById("character-list");
    const instructions = document.getElementById("selection-instructions");
    const confirmButton = document.getElementById("confirm-character-selection");
    const selectionOrder = document.getElementById("selection-order");

    if (!modal || !characterList || !instructions || !confirmButton || !selectionOrder) {
        console.error("Modal or required elements not found in DOM.");
        return;
    }

    const maxSelection = gameType === "double" ? 2 : 1;

    // Update the instructions
    instructions.textContent = `Please select ${maxSelection} character${maxSelection > 1 ? 's' : ''}.`;

    // Populate the character list
    characterList.innerHTML = characters
        .map(character =>
            `<label>
                <input type="${gameType === "double" ? "checkbox" : "radio"}" 
                       name="character" value="${character}" 
                       onchange="handleCharacterSelection('${gameType}')">
                ${character}
            </label>`
        )
        .join("<br>");

    // Clear previous selections and disable the confirm button
    confirmButton.disabled = true;
    selectionOrder.textContent = '';

    modal.style.display = "block";
}


function handleCharacterSelection(gameType) {
    const maxSelection = gameType === "double" ? 2 : 1;
    const selected = Array.from(document.querySelectorAll("input[name='character']:checked"));
    const allInputs = document.querySelectorAll("input[name='character']");
    const confirmButton = document.getElementById("confirm-character-selection");
    const selectionOrder = document.getElementById("selection-order");

    // Update the confirm button state
    confirmButton.disabled = selected.length !== maxSelection;

    // Disable additional checkboxes if the max selection is reached
    allInputs.forEach(input => {
        if (!input.checked && selected.length >= maxSelection) {
            input.disabled = true;
        } else {
            input.disabled = false;
        }
    });

    // Display the order of selected characters or placeholder
    if (selected.length === 0) {
        selectionOrder.textContent = "No characters selected yet.";
    } else if (gameType === "double") {
        selectionOrder.textContent = `1st: ${selected[0]?.value || ''}${
            selected[1] ? `, 2nd: ${selected[1]?.value}` : ''
        }`;
    } else {
        selectionOrder.textContent = `Selected: ${selected[0]?.value}`;
    }
}



function toggleCharacterModal(show) {
    const modal = document.getElementById("character-modal");

    if (!modal) {
        console.error("Character modal not found in DOM.");
        return;
    }

    if (show) {
        modal.style.display = "flex"; // Ensure centering by setting flex
    } else {
        modal.style.display = "none"; // Hide modal
    }
}

function confirmCharacterSelection() {
    const selected = Array.from(document.querySelectorAll("input[name='character']:checked"))
        .map(input => input.value);

    const gameType = document.getElementById("game-select").dataset.gameType; // Fetch game type from data attribute
    const characterInput = document.getElementById("env-setting-characters");

    if (!characterInput) return;

    const maxSelection = gameType === "double" ? 2 : 1;

    if (selected.length !== maxSelection) {
        alert(`Please select exactly ${maxSelection} character${maxSelection > 1 ? 's' : ''}.`);
        return;
    }

    characterInput.value = selected.join(", ");
    toggleCharacterModal(false);
}


function initializeListenersForTrainingDashboard() {
    const gameSelect = document.getElementById("game-select");

    if (gameSelect) {
        // Auto-select the first game if none is selected
        if (!gameSelect.value) {
            gameSelect.value = gameSelect.options[0]?.value;
            console.log(`No game selected, defaulting to: ${gameSelect.value}`);
            initializeGameSelectListener(gameSelect.value); // Populate environment settings for the default selection
        }

        // Remove any existing event listeners to prevent duplication
        gameSelect.removeEventListener("change", handleGameChange);
        gameSelect.addEventListener("change", handleGameChange);
    }

    async function handleGameChange(event) {
        const gameId = event.target.value;
        await initializeGameSelectListener(gameId);
    }

    // Initialize additional components
    initializeCharacterSelectListener();
    initializeConfigManager();
    initializeTooltips();
    initializeLogStreaming();
    initializeVideoFeed();
    initializeBatchSizeDropdown();
    initializeFilterKeysDropdown();

    console.log("Listeners for Training Dashboard initialized.");
}
