# BuddyAI: Your AI-Powered Desktop Assistant 🤖✨

**BuddyAI is an open-source, extensible desktop assistant that uses Large Language Models (like Google's Gemini) to understand your commands in plain English and execute tasks on your local machine.**

Ever wanted to just *tell* your computer what to do? BuddyAI aims to make that a reality. Whether it's creating files, searching the web, getting system information, or managing your reminders, just type your request, and let BuddyAI (powered by an LLM) handle the rest.


## Features

*   **Natural Language Command Interface:** Speak to your computer in plain English.
*   **LLM-Powered Interpretation:** Leverages Google's Gemini API (initially) to understand your intent and translate it into actionable commands.
*   **Local Task Execution:** Commands are executed securely on your own machine by a local agent.
*   **Extensible Agent Capabilities:** Easily add new commands and functionalities by creating simple Python modules. The system dynamically discovers these new capabilities.
*   **Cross-Platform (Goal):** Core logic is Python-based, aiming for compatibility with Windows, macOS, and Linux. (OS-specific commands like volume control or app closing will have varying levels of support).
*   **User-Provided API Key:** You use your *own* LLM API key, ensuring you control your usage and costs.
*   **Open Source:** Fork it, extend it, contribute back!

## How It Works

BuddyAI consists of two main components that run on your local machine:

1.  **The Controller (`controller.py`):**
    *   Takes your plain English input.
    *   Communicates with the configured LLM (e.g., Gemini) to parse your input and translate it into a structured JSON command.
    *   Dynamically fetches the list of available commands and their parameters from the Agent Server.
    *   Sends the structured command to the Agent Server for execution.
    *   Displays the results back to you.

2.  **The Agent Server (`agent/agent_server.py`):**
    *   A lightweight Flask server that runs locally.
    *   On startup, it dynamically loads "command modules" from the `agent/modules/` directory.
    *   Exposes an `/execute` endpoint to receive structured JSON commands from the Controller.
    *   Executes the requested command using the corresponding Python function from its loaded modules.
    *   Exposes a `/commands_schema` endpoint that the Controller uses to learn about available commands and their expected parameters.

This architecture allows for a clear separation of concerns and makes the agent highly extensible.

## Tech Stack

*   **Python 3.9+**
*   **Google Gemini API:** For Natural Language Understanding and command generation.
*   **Flask:** For the local Agent Server.
*   **Pydantic:** For data validation and schema definition used with the Gemini API.
*   **Requests:** For HTTP communication between Controller and Agent.
*   **Standard Python Libraries:** `os`, `subprocess`, `platform`, `shutil`, `webbrowser`, `inspect`, etc.
*   **External Libraries (for some agent modules):**
    *   `psutil`: For system load, and advanced application closing.
    *   `Pillow (PIL)`: For taking screenshots.
    *   `pyperclip`: For clipboard operations.
    *   `pycaw` (Windows-only): For system volume control on Windows. (Linux/macOS use system commands).

## Prerequisites

*   **Python 3.9** or higher installed.
*   **`pip`** (Python package installer).
*   **Git** (for cloning the repository).
*   A **Google Gemini API Key**. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).
*   **(Optional, for specific agent commands on Linux):** `xclip` or `xsel` for clipboard functionality if `pyperclip` requires it. `amixer` (alsa-utils) or `pactl` (pulseaudio-utils) for volume control.

## Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/MockingJay1710/buddyai.git
    cd buddyai
    ```

2.  **Create and Activate a Python Virtual Environment:**
    *   **Linux/macOS:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(This will install Flask, Requests, google-generativeai, Pydantic, python-dotenv, and optional libraries like psutil, Pillow, pyperclip, pycaw).*

4.  **Set Up Your Gemini API Key:**
    *   Create a file named `.env` in the root directory of the project (the same directory as `controller.py`).
    *   Add your Gemini API key to this file:
        ```env
        # .env
        GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
        # Optional: You can also specify the agent URL if you change its port
        # AGENT_URL="http://127.0.0.1:5000/execute"
        ```
    *   **IMPORTANT:** The `.env` file is included in `.gitignore` and should never be committed to your repository.

## Running BuddyAI

You need to run two components in separate terminal windows (both with the virtual environment activated):

1.  **Start the Agent Server:**
    Open a terminal, navigate to the project root, and run:
    ```bash
    python agent/agent_server.py
    ```
    You should see output indicating that modules are being loaded and the Flask server is running (e.g., on `http://127.0.0.1:5000/`).

2.  **Start the Controller (User Interface):**
    Open another terminal, navigate to the project root, and run:
    ```bash
    python controller.py
    ```
    The controller will attempt to fetch the command schema from the agent. You can then start typing commands!

## Usage Examples

Once both components are running, you can type commands into the controller's prompt:

*   `"What time is it on the server?"`
*   `"Create a file named hello.txt with the content 'Welcome to BuddyAI'"`
*   `"Read the file hello.txt"`
*   `"Open Google Chrome"`
*   `"Search the web for 'how to make a good README'"`
*   `"Take a screenshot and save it as main_screen.png"`
*   `"Set a reminder for 10 minutes from now to stretch"` (Note: Current reminder time parsing might require more specific formats like "HH:MM" or "YYYY-MM-DD HH:MM")
*   `"What's on my clipboard?"`

Explore the different modules in `agent/modules/` to see the full range of currently implemented commands!

## Extending BuddyAI: Adding New Commands

One of the core strengths of BuddyAI is its extensibility. To add a new command:

1.  **Create or Choose a Module:**
    *   Navigate to the `agent/modules/` directory.
    *   You can add your function to an existing relevant module (e.g., a new file operation to `file_system_ops.py`) or create a new Python file for a new category of commands (e.g., `email_ops.py`).

2.  **Write Your Command Function:**
    *   Define a Python function that performs the desired action.
    *   The function should accept parameters as needed.
    *   It should return a dictionary, typically including a `"status": "success"` or `"status": "error"` key, along with any relevant data or a `"message"` key.
    *   **Crucially, add a clear docstring and type hints to your function and its parameters.** The first line/paragraph of the docstring will be used as the command's description for the LLM. Type hints and default values help define the parameter schema.

    ```python
    # Example in a new module agent/modules/my_new_ops.py
    def my_custom_action(target_object: str, setting_value: int = 10):
        """
        Performs a custom action on a target object with a specific setting.

        This is an example of how to document a new command function.
        The LLM will use this description to understand when to call this command.

        Args:
            target_object (str): The name or identifier of the object to act upon.
            setting_value (int, optional): The value for the setting. Defaults to 10.
        """
        try:
            # ... your logic here ...
            result_message = f"Custom action performed on '{target_object}' with setting {setting_value}."
            return {"status": "success", "message": result_message, "details": "some_details_if_any"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to perform custom action: {e}"}
    ```

3.  **Register Your Command:**
    *   At the bottom of your module file, add or update the `COMMANDS` dictionary to map a unique command name (which the LLM will use) to your function:
    ```python
    # At the end of agent/modules/my_new_ops.py
    COMMANDS = {
        "custom_do_something": my_custom_action,
        # ... other commands from this module
    }
    ```

4.  **Restart the Agent Server:**
    *   Stop and restart `agent/agent_server.py`. It will automatically discover your new module/command and load it.

5.  **Restart the Controller:**
    *   Stop and restart `controller.py`. It will fetch the updated command schema from the agent, including your new command.

You can now try invoking your new command using natural language!

## Troubleshooting

*   **`404 Client Error: NOT FOUND for url: http://127.0.0.1:5000/commands_schema` (Controller):**
    *   Ensure `agent/agent_server.py` is running.
    *   Verify that the `agent_server.py` code contains the `@app.route('/commands_schema', methods=['GET'])` endpoint and that you are running the latest saved version of the file.
*   **`405 Client Error: METHOD NOT ALLOWED for url: http://127.0.0.1:5000/` (Controller):**
    *   Make sure `AGENT_URL` in `controller.py` (or your `.env` file) is set correctly to include the `/execute` path (e.g., `http://127.0.0.1:5000/execute`).
*   **LLM picks the wrong command or fails to extract parameters:**
    *   **Check Agent Docstrings:** Ensure the docstring for the intended command function (in the agent module) is clear, descriptive, and uses keywords the LLM would associate with that task.
    *   **Check Controller's Formatted Schema:** In `controller.py`, uncomment the `print(f"Formatted Schema:\n{AGENT_COMMANDS_SCHEMA_STRING}")` line in `fetch_and_format_agent_commands_schema()` to see the exact schema description being sent to Gemini. Is it accurate?
    *   **Refine Controller Prompt:** You might need to adjust the main system prompt given to Gemini in `controller.py` to be more directive about choosing the best command or formatting parameters.
    *   **Be Specific with Your Input:** Try phrasing your natural language command differently.
*   **Module specific errors (e.g., `psutil not found`):**
    *   Make sure you've installed all necessary libraries from `requirements.txt` and any optional ones listed for specific modules you intend to use.

## Contributing

Contributions are welcome and greatly appreciated! Whether it's reporting a bug, suggesting a feature, improving documentation, or writing code, please feel free to get involved.

1.  **Reporting Bugs / Suggesting Features:** Please open an issue on the [GitHub Issues page](https://github.com/MockingJay1710/buddyai.git/issues).
2.  **Contributing Code:**
    *   Fork the repository.
    *   Create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name` or `git checkout -b fix/your-bug-fix`).
    *   Make your changes. Remember to add good docstrings and type hints for new agent commands.
    *   Ensure your code passes any linters/formatters if set up (or generally adheres to PEP 8).
    *   Commit your changes (`git commit -am 'Add some amazing feature'`).
    *   Push to your forked branch (`git push origin feature/your-feature-name`).
    *   Open a Pull Request against the `main` branch of this repository.
    *   Clearly describe your changes in the Pull Request.

Please refer to `CONTRIBUTING.md` for more detailed guidelines. (TODO: Create a CONTRIBUTING.md file)

## Roadmap (Potential Future Ideas)

*   **GUI:** Develop a graphical user interface (e.g., using PyQt, Tkinter, or a web UI).
*   **Contextual Conversation Memory:** Allow for follow-up commands that understand previous interactions.
*   **Pluggable LLM Providers:** Support for other LLMs beyond Gemini (e.g., OpenAI GPT models, local LLMs).
*   **Persistent Reminders:** Store reminders in a file or database so they survive agent restarts.
*   **User-Defined Aliases/Shortcuts for Commands.**
*   **Configuration UI:** A settings panel within the application for API keys, agent port, etc.
*   **Executable Packaging:** Provide pre-built executables for Windows, macOS, and Linux.
*   **More Advanced Agent Capabilities:** E.g., email interaction, calendar integration, more complex scripting.
*   **Improved Error Handling and User Feedback from the LLM.**

## License

This project is licensed under the **MIT License**. See the `LICENSE.md` file for details.

---

Thank you for checking out BuddyAI! We hope you find it useful and fun to experiment with.