// path: app/static/js/settings.js

function initializeListenersForSettingsMenu() {
    // Initialize login modal functionality
    initializeLoginModal();

    // Check if credentials file exists and update UI
    checkCredentialsFile();

    // Initialize token form submission
    initializeTokenForm();

    // Initialize open folder buttons
    initializeOpenFolderButtons();

    console.log("Listeners for Settings Menu initialized.");
}

function initializeLoginModal() {
    const loginModal = document.getElementById("login-modal");
    const openLoginModalBtn = document.getElementById("open-login-modal");
    const closeLoginModalBtn = document.getElementById("close-login-modal");
    const saveTokenBtn = document.getElementById("save-modal-token");
    const tokenInput = document.getElementById("modal-token");

    if (openLoginModalBtn && loginModal && closeLoginModalBtn && saveTokenBtn && tokenInput) {
        // Open modal when button is clicked
        openLoginModalBtn.addEventListener("click", () => {
            loginModal.style.display = "block";
        });

        // Close modal when close button is clicked
        closeLoginModalBtn.addEventListener("click", () => {
            loginModal.style.display = "none";
        });

        // Close modal when clicking outside the modal content
        window.addEventListener("click", (event) => {
            if (event.target === loginModal) {
                loginModal.style.display = "none";
            }
        });

        // Save token when "Save Token" button is clicked
        saveTokenBtn.addEventListener("click", async () => {
            const token = tokenInput.value.trim();
            if (!token) {
                alert("Please paste a valid token.");
                return;
            }

            await saveToken(token);
            loginModal.style.display = "none";
        });
    } else {
        console.error("Login modal elements not found.");
    }
}

async function checkCredentialsFile() {
    console.log("Checking credentials file...");

    try {
        const response = await fetch("/settings/check-credentials");

        // Check for HTTP errors
        if (!response.ok) {
            console.error("Failed to fetch credentials check. Status:", response.status);
            return false;
        }

        const result = await response.json();
        console.log("Credentials check response:", result);

        // Validate the `result.exists` value
        if (typeof result.exists !== "boolean") {
            console.error("Invalid response format. 'exists' field is missing or not a boolean.");
            return false;
        }

        // Update UI based on credentials existence
        const warning = document.getElementById("credentials-warning");
        const success = document.getElementById("credentials-success");
        if (!result.exists) {
            if (warning) warning.style.display = "block";
            if (success) success.style.display = "none";
            console.log("Credentials missing. Warning displayed.");
        } else {
            if (warning) warning.style.display = "none";
            if (success) success.style.display = "block";
            console.log("Credentials exist. Success displayed.");
        }

        return result.exists;
    } catch (error) {
        console.error("Error checking credentials file:", error);
        return false;
    }
}

function initializeTokenForm() {
    const tokenForm = document.getElementById("update-token-form");
    const tokenInput = document.getElementById("token");

    if (tokenForm && tokenInput) {
        tokenForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const token = tokenInput.value.trim();
            if (!token) {
                alert("Please enter a token.");
                return;
            }
            await saveToken(token);
        });
    } else {
        console.error("Token form elements not found.");
    }
}

async function saveToken(token) {
    try {
        const response = await fetch("/settings/save-token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ token }),
        });

        const result = await response.json();
        if (response.ok) {
            alert(result.message || "Token saved successfully.");
            const warning = document.getElementById("credentials-warning");
            const success = document.getElementById("credentials-success");
            if (warning) warning.style.display = "none";
            if (success) success.style.display = "block";
        } else {
            alert(result.error || "An error occurred.");
        }
    } catch (error) {
        console.error("Error saving token:", error);
        alert("An error occurred while saving the token.");
    }
}

// Initialize the "Open Checkpoints" and "Open Logs" buttons
function initializeOpenFolderButtons() {
    const openCheckpointsBtn = document.getElementById("open-checkpoints");
    const openLogsBtn = document.getElementById("open-logs");

    function openFolder(url, button) {
        if (button.disabled) return; // Prevents multiple clicks

        button.disabled = true; // Temporarily disable the button
        fetch(url, { method: "GET" })
            .catch(error => console.error(`Error opening folder: ${error}`))
            .finally(() => {
                setTimeout(() => (button.disabled = false), 500); // Re-enable after 500ms
            });
    }

    if (openCheckpointsBtn) {
        openCheckpointsBtn.addEventListener("pointerdown", () => openFolder("/settings/open-checkpoints", openCheckpointsBtn));
    }

    if (openLogsBtn) {
        openLogsBtn.addEventListener("pointerdown", () => openFolder("/settings/open-logs", openLogsBtn));
    }
}