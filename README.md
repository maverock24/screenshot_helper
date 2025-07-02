# AI Screenshot & Audio Helper

A collection of powerful utilities for Linux desktops that provide AI-powered analysis for visual and audio content.

Perfect for understanding complex code, deciphering error messages, analyzing audio content, or answering questions found anywhere on your screen or in audio recordings.

## Features

### Screenshot Analysis
-   **One-Press Activation:** Triggered by a global keyboard shortcut.
-   **Instant Full-Screen Capture:** No need to select a region; it captures everything instantly.
-   **AI-Powered Analysis:** Uses Google's Gemini model to analyze the image.
-   **Loading Indicator:** A "Thinking..." pop-up provides feedback while waiting for the AI.
-   **Formatted Output:** Displays the AI's response in a clean, readable pop-up with scrollbars.
-   **Highly Configurable:** Easily change the AI prompt, window size, and more by editing the script.

### Audio Analysis
-   **GUI Interface:** Simple window with record/stop buttons for easy operation.
-   **System Audio Recording:** Records audio playing through your speakers (not microphone input).
-   **Real-time Status:** Visual feedback showing recording status and processing updates.
-   **AI-Powered Transcription:** Analyzes audio content including speech, music, and background sounds.
-   **Meeting Support:** Perfect for analyzing Teams meetings, YouTube videos, or any system audio.
-   **Browser Results:** Opens detailed AI analysis in a new browser tab with formatted output.

## Prerequisites

1.  A Debian-based Linux system (e.g., Ubuntu 22.04+, Linux Mint, etc.) running on X11.
2.  A **Google AI API Key**. You can get one for free from [Google AI Studio](https://aistudio.google.com/).

## Installation

The installation process is automated with a simple script.

1.  **Download the files:**
    Clone this repository or download all the files into a new folder on your computer.

    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Run the Installer:**
    Open a terminal in the project folder and run the installer script. It will guide you through the process and install all dependencies for both screenshot and audio features.

    ```bash
    # First, make the installer executable
    chmod +x install.sh

    # Then, run it
    ./install.sh
    ```
    The script will ask for your password to install system packages (including audio recording tools) and will prompt you to enter your Google AI API key. At the end, it will print the exact command you need for the keyboard shortcut.

## Usage

### Screenshot Tool

The only remaining step is to create a global keyboard shortcut to run the tool.

1.  Open your system **Settings**.
2.  Navigate to the **Keyboard** section.
3.  Find **Custom Shortcuts** (or "Keyboard Shortcuts" and scroll to the bottom).
4.  Click the `+` button to add a new shortcut.
5.  Fill in the fields:
    * **Name:** `AI Screenshot Helper`
    * **Command:** Paste the full command that was printed at the end of the installation script. It will look something like this: `/home/your_username/path/to/project/.venv/bin/python /home/your_username/path/to/project/explain_screenshot.py`
    * **Shortcut:** Click "Set Shortcut..." and press the key combination you want to use (e.g., `Ctrl` + `Shift` + `S`).

That's it! Close the settings and press your new shortcut to try it out.

### Audio Tool

The audio analysis tool has its own GUI interface:

1.  **Launch the application:**
    ```bash
    cd /path/to/project
    ./.venv/bin/python explain_audio.py
    ```

2.  **Record audio:**
    - Click "Start Recording" to begin capturing system audio
    - Play any audio (YouTube videos, Teams meetings, music, etc.)
    - Click "Stop Recording" when finished

3.  **View results:**
    - The AI analysis will automatically open in your browser
    - Results include transcription and detailed content analysis

## Configuration

### Screenshot Tool

You can easily customize the screenshot tool by editing the `explain_screenshot.py` script:

-   **Window Size:** To change the size of the results pop-up, adjust the percentage values at the top of the script:
    ```python
    MAX_HEIGHT_PERCENT = 0.7  # 70% of screen height
    MAX_WIDTH_PERCENT = 0.6   # 60% of screen width
    ```

-   **AI Prompt:** To change the instructions for the AI, edit the `PROMPT` variable:
    ```python
    PROMPT = "Explain the code, question, or error message in this screenshot..."
    ```

### Audio Tool

You can customize the audio analysis by editing the `explain_audio.py` script:

-   **AI Prompt:** To change the instructions for audio analysis, edit the `PROMPT` variable:
    ```python
    PROMPT = "Analyze this audio recording and provide detailed answers..."
    ```

-   **Audio Quality:** Modify the recording parameters in the `start_recording()` method for different quality settings.

## Files in this Project

-   `README.md`: This file.
-   `install.sh`: The automated installer script.
-   `explain_screenshot.py`: The screenshot analysis application.
-   `explain_audio.py`: The audio analysis application.
-   `.venv/`: A folder created by the installer containing the Python virtual environment.
-   `.env`: A file created by the installer that securely stores your API key.