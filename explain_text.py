#!/usr/bin/env python3

import os
import sys
import subprocess
import webbrowser
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import markdown
from pygments.formatters import HtmlFormatter

# --- SCRIPT CONFIGURATION ---
# This is the default prompt that appears in the input window.
DEFAULT_PROMPT = "Summarize this text and identify key takeaways."

# --- MAIN SCRIPT ---

def get_selected_text():
    """Gets the currently highlighted text using xclip."""
    print("Getting selected text...")
    try:
        # The '-o' flag prints the selection to standard output.
        selected_text = subprocess.check_output(["xclip", "-o"], text=True)
        if not selected_text.strip():
            show_error_popup("No Text Selected", "You must highlight some text before running the script.")
            return None
        return selected_text
    except FileNotFoundError:
        show_error_popup("Dependency Missing", "The 'xclip' utility is not installed. Please run: sudo apt install xclip")
        return None
    except subprocess.CalledProcessError:
        # This can happen if no text is selected.
        show_error_popup("No Text Selected", "You must highlight some text before running the script.")
        return None

def get_user_prompt():
    """Opens an input window using yad to get instructions from the user."""
    print("Opening prompt window...")
    try:
        # --entry shows an input box. --text provides the instructions.
        # The output of the command is the text the user entered.
        user_prompt = subprocess.check_output([
            "yad", "--entry",
            "--title=AI Text Helper",
            "--text=What should I do with the selected text?",
            f"--entry-text={DEFAULT_PROMPT}",
            "--width=500"
        ], text=True).strip()
        
        return user_prompt if user_prompt else None

    except subprocess.CalledProcessError:
        # This happens if the user closes the window or clicks Cancel.
        print("User cancelled the prompt window.")
        return None
    except FileNotFoundError:
        show_error_popup("Dependency Missing", "The 'yad' utility is not installed. Please run: sudo apt install yad")
        return None


def format_as_html(text: str) -> str:
    """Converts the AI's markdown response into a full HTML document."""
    print("Formatting response as HTML...")
    html_fragment = markdown.markdown(
        text, extensions=['fenced_code', 'codehilite']
    )
    formatter = HtmlFormatter(style='default', full=True, cssclass="codehilite")
    css_styles = formatter.get_style_defs()
    
    full_html = f"""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>AI Text Helper</title>
    <style>
        body {{font-family: sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 20px;}}
        {css_styles} .codehilite {{padding: 1em; border-radius: 8px; overflow-x: auto;}}
        img {{max-width: 100%;}}
    </style></head><body>{html_fragment}</body></html>
    """
    return full_html

def create_and_show_html(html_content: str):
    """Saves content to a temporary HTML file and opens it in a browser."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
            f.write(html_content)
            filepath = f.name
        print(f"Temporary HTML file created at: {filepath}")
        webbrowser.open_new_tab(f'file://{os.path.realpath(filepath)}')
    except Exception as e:
        print(f"FATAL: Could not create or open the HTML file. Error: {e}", file=sys.stderr)

def get_ai_explanation(selected_text: str, user_prompt: str):
    """Sends the selected text and user prompt to the Gemini API."""
    print("Sending text to AI for explanation...")
    try:
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("FATAL: GOOGLE_API_KEY not found in .env file.", file=sys.stderr)
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Construct a clear, combined prompt for the AI
        full_prompt = f"INSTRUCTION: '{user_prompt}'\n\nApply the above instruction to the following text:\n\n---\n{selected_text}\n---"
        
        response = model.generate_content(full_prompt)
        print("AI response received.")
        return response.text
    except Exception as e:
        print(f"FATAL: Error contacting AI model. Error: {e}", file=sys.stderr)
        return None

def show_error_popup(title, text):
    """Displays an error popup window using yad."""
    try:
        subprocess.run(["yad", "--error", "--title", title, "--text", text, "--width=350"], check=True)
    except FileNotFoundError:
        print(f"\n--- ERROR: {title} ---\n{text}", file=sys.stderr)

if __name__ == "__main__":
    # The new workflow for selected text
    selected_text = get_selected_text()
    if selected_text:
        user_prompt = get_user_prompt()
        if user_prompt:
            explanation = get_ai_explanation(selected_text, user_prompt)
            if explanation:
                html_output = format_as_html(explanation)
                create_and_show_html(html_output)