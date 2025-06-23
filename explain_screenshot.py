#!/usr/bin/env python3

import os
import sys
import subprocess
import re
import webbrowser
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import markdown
from pygments.formatters import HtmlFormatter

# --- USER CONFIGURATION ---
# (No longer need window size percentages)

# --- SCRIPT CONFIGURATION ---
PROMPT = "Explain the code, question, or error message in this screenshot and solve it if possible. Provide a clear and concise explanation or solution. Also if possible provide solution in typescript."
SCREENSHOT_PATH = Path.home() / "temp_screenshot.png"

# --- MAIN SCRIPT ---

def take_screenshot():
    """Takes a screenshot of the entire screen using maim (for X11)."""
    print("Preparing full-screen screenshot with maim...")
    try:
        # The -s flag selects a region. Remove it for full-screen.
        # We add a small delay to ensure the desktop is ready.
        subprocess.run(["maim", "-d", "1", str(SCREENSHOT_PATH)], check=True)
        if not SCREENSHOT_PATH.exists() or SCREENSHOT_PATH.stat().st_size == 0:
            print("Screenshot failed or was cancelled.")
            return False
        print(f"Screenshot saved to {SCREENSHOT_PATH}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        # Using a simple print for errors now, as we're avoiding GUI popups
        print(f"FATAL: Screenshot failed. Is 'maim' installed? Error: {e}", file=sys.stderr)
        return False

def format_as_html(text: str) -> str:
    """
    Converts the AI's markdown response into a full HTML document with syntax highlighting.
    """
    print("Formatting response as HTML...")
    # Convert the core markdown text to an HTML fragment.
    # 'fenced_code' allows for ```python ... ``` blocks.
    # 'codehilite' integrates with Pygments for syntax highlighting.
    html_fragment = markdown.markdown(
        text, extensions=['fenced_code', 'codehilite']
    )

    # Get the CSS for the syntax highlighting theme ('default' is a nice light theme)
    formatter = HtmlFormatter(style='default', full=True, cssclass="codehilite")
    css_styles = formatter.get_style_defs()
    
    # Wrap the fragment in a full HTML document with embedded styles
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Screenshot Helper</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
            }}
            {css_styles}
            .codehilite {{
                padding: 1em;
                border-radius: 8px;
                overflow-x: auto;
            }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        {html_fragment}
    </body>
    </html>
    """
    return full_html

def create_and_show_html(html_content: str):
    """Saves content to a temporary HTML file and opens it in a new browser tab."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
            f.write(html_content)
            filepath = f.name
            print(f"Temporary HTML file created at: {filepath}")

        # Open the file in a new browser tab
        webbrowser.open_new_tab(f'file://{os.path.realpath(filepath)}')

    except Exception as e:
        print(f"FATAL: Could not create or open the HTML file. Error: {e}", file=sys.stderr)

def get_ai_explanation():
    """Sends the screenshot to the Gemini API and returns the explanation."""
    print("Sending screenshot to AI for explanation...")
    try:
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("FATAL: GOOGLE_API_KEY not found in .env file.", file=sys.stderr)
            return None
        
        genai.configure(api_key=api_key)
        img = Image.open(SCREENSHOT_PATH)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([PROMPT, img])
        print("AI response received.")
        return response.text
    except Exception as e:
        print(f"FATAL: Error contacting AI model. Error: {e}", file=sys.stderr)
        return None
    finally:
        if SCREENSHOT_PATH.exists():
            os.remove(SCREENSHOT_PATH)

if __name__ == "__main__":
    if take_screenshot():
        explanation = get_ai_explanation()
        if explanation:
            html_output = format_as_html(explanation)
            create_and_show_html(html_output)