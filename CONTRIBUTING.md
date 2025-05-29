# Contributing to BuddyAI

First off, thank you for considering contributing to BuddyAI! We're excited to build a vibrant community around this project and believe that with your help, BuddyAI can become an incredibly powerful and versatile tool.

This document provides guidelines for contributing. We welcome contributions of all kinds, from bug reports and documentation improvements to new features and architectural enhancements.

## How Can I Contribute?

*   **Reporting Bugs:** If you find a bug, please open an issue on our [GitHub Issues page](https://github.com/MockingJay1710/buddyai.git/issues). Provide as much detail as possible, including steps to reproduce.
*   **Suggesting Enhancements or New Features:** Have an idea? We'd love to hear it! Open an issue to discuss it.
*   **Writing Code:** Help us expand BuddyAI's capabilities or improve its core.
*   **Improving Documentation:** Clear documentation is key. If you see areas for improvement, let us know or submit a PR.

## Areas We're Actively Looking for Contributions In

While all contributions are welcome, here are some areas where your help would be particularly impactful in growing BuddyAI:

### 1. Expanding Agent Capabilities (Adding New Command Modules/Plugins)

This is the primary way to make BuddyAI more powerful and versatile for everyone!

*   **What we're looking for:**
    *   New Python modules for the `agent/modules/` directory that add new functionalities (e.g., interacting with specific APIs, managing system settings not yet covered, integrating with other applications, creative productivity tools).
    *   Improvements to existing modules (e.g., making them more robust, adding more options, better OS compatibility).
*   **How to contribute:**
    *   Review the existing modules in `agent/modules/` to understand the pattern.
    *   Create a new Python file (e.g., `my_new_feature_ops.py`) or modify an existing one.
    *   Define your Python function(s) that perform the desired action.
    *   **Crucially:** Add clear **docstrings** (the first line/paragraph is the description for the LLM) and **type hints** for all parameters.
    *   Register your function(s) in the `COMMANDS` dictionary at the bottom of your module file.
    *   See the "Extending BuddyAI" section in `README.md` for a detailed guide.
*   **Ideas (but feel free to propose your own!):**
    *   Email sending/reading (via local client or API).
    *   Calendar integration (reading events, creating events).
    *   Integration with specific cloud services (e.g., upload file to S3/Google Drive).
    *   Advanced window management.
    *   Controlling smart home devices (if a local API is available).

### 2. Developing a Graphical User Interface (GUI)

Currently, BuddyAI uses a command-line interface for the controller. A GUI would make it much more accessible and user-friendly.

*   **What we're looking for:**
    *   Proposals and implementations for a desktop GUI.
    *   Considerations: Cross-platform compatibility (Windows, macOS, Linux), ease of use, clean design.
*   **Potential Technologies (but open to suggestions):**
    *   PyQt / PySide
    *   Tkinter (for a simpler, lightweight option)
    *   Kivy
    *   A web-based UI served locally by the controller (e.g., using Flask/FastAPI for the backend and HTML/JS/CSS for the frontend).
*   **Key GUI Features:**
    *   Input field for natural language commands.
    *   Area to display conversation history and agent responses.
    *   Settings panel for API key configuration and potentially other preferences.
    *   Ability to easily start/stop the background agent server (if packaged together).
*   **How to contribute:**
    *   This is a larger undertaking. Please **open an issue first** to discuss your approach, chosen technology, and design ideas before starting significant development. This helps ensure alignment with the project's direction.

### 3. Enhancing User Interaction & LLM Integration

*   **Contextual Conversation Memory:** Implement a system where the controller remembers the last few interactions to allow for follow-up commands (e.g., "List files." -> "Delete the second one.").
*   **Pluggable LLM Providers:** Abstract the LLM interaction logic in `controller.py` to potentially support other models (e.g., OpenAI GPT, local LLMs via libraries like `llama-cpp-python`). This would likely involve defining an interface for LLM interaction.
*   **Improved Error Handling & Feedback:** Make error messages more user-friendly, potentially using the LLM to explain technical errors or suggest alternative commands.
*   **User-Defined Aliases/Shortcuts:** Allow users to define their own short phrases for common or complex commands.

### 4. Core System Improvements & Robustness

*   **Persistent Reminders:** Modify the reminder system in `productivity_ops.py` to save reminders to a file or local database so they persist across agent restarts.
*   **Configuration Management:** A more structured way to manage settings beyond the `.env` file, perhaps a `config.json` or `config.yaml` that could be edited via a future GUI.
*   **Automated Testing:** Adding unit tests and integration tests for agent modules and controller logic. This is crucial for long-term stability.
*   **Executable Packaging & Distribution:** Help with creating reliable installers and packaged executables for Windows, macOS, and Linux using tools like PyInstaller, Briefcase, etc.

## Getting Started (General Code Contributions)

1.  **Fork the Repository:** [Link to your repo's fork button]
2.  **Clone Your Fork:** `git clone https://github.com/YOUR_USERNAME/buddyai.git`
3.  **Set Up Environment:** Follow `README.md` for installation.
4.  **Create a New Branch:** `git checkout -b your-branch-name`
    *   Good branch names: `feature/add-email-module`, `fix/clipboard-error-linux`, `docs/improve-readme-setup`

## Making Changes

1.  **Write Your Code:** Adhere to existing code style (PEP 8).
2.  **Test Thoroughly:** Ensure your changes work and don't break anything.
3.  **Commit Your Changes:** Write clear, descriptive commit messages.
    *   Example: `git commit -m "feat(agent): Add email sending capability via SMTP"`
4.  **Push to Your Fork:** `git push origin your-branch-name`

## Submitting a Pull Request (PR)

1.  Open a PR from your branch on your fork to the `main` (or `develop`) branch of the upstream repository.
2.  **Write a Clear PR Description:**
    *   Explain *what* your PR does and *why*.
    *   Link to any relevant issues (e.g., "Closes #123").
    *   Provide testing steps for reviewers.
3.  Submit the PR. We'll review it as soon as possible!

## Code Review & Discussion

*   Be open to feedback and discussion during the code review process.
*   Changes might be requested to ensure quality, consistency, and alignment with the project's goals.

## Code of Conduct

We do not yet have certain standars or rules for your code to follow, it should just be clear, well commented and modular.

## Questions?

If you're unsure where to start, have questions about a specific area, or want to discuss an idea, please don't hesitate to open an issue!

We're excited to see your contributions and build something amazing together!