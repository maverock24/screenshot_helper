#!/usr/bin/env python3

import os
import sys
import threading
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import webbrowser
import markdown
from pygments.formatters import HtmlFormatter
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

PROMPT_SCREENSHOT = "Explain the code, question, or error message in this screenshot and solve it if possible. Provide a clear and concise explanation or solution. Also if possible provide solution in typescript."
PROMPT_AUDIO = "Analyze this audio recording and provide a detailed answers of questions you hear and if possible provide a solution in typescript."
PROMPT_VIDEO = "Analyze this video recording and provide a detailed explanation of what is happening. If possible, answer any questions or errors shown in the video and provide a solution in typescript."
PROMPT_TEXT = "Explain the following text/code or error message and provide a solution in typescript if possible."

SCREENSHOT_PATH = Path.home() / "temp_screenshot.png"
AUDIO_PATH = Path.home() / "temp_audio_recording.wav"
VIDEO_PATH = Path.home() / "temp_video_recording.mp4"

class AIHelperSuite:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Helper Suite")
        self.root.geometry("600x420")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.create_screenshot_tab()
        self.create_audio_tab()
        self.create_video_tab()
        self.create_text_tab()

    def create_screenshot_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Screenshot")
        label = ttk.Label(tab, text="AI Screenshot Helper", font=("Arial", 14, "bold"))
        label.pack(pady=(18, 8))
        desc = ttk.Label(tab, text="Take a screenshot and get an AI explanation or solution.")
        desc.pack(pady=(0, 10))
        self.ss_status = ttk.Label(tab, text="Ready.")
        self.ss_status.pack(pady=(0, 10))
        btn = ttk.Button(tab, text="Capture Screenshot", command=self.capture_screenshot)
        btn.pack(pady=(0, 10))

    def capture_screenshot(self):
        self.ss_status.config(text="Capturing screenshot...")
        def worker():
            try:
                subprocess.run(["maim", "-d", "1", str(SCREENSHOT_PATH)], check=True)
                if not SCREENSHOT_PATH.exists() or SCREENSHOT_PATH.stat().st_size == 0:
                    self.ss_status.config(text="Screenshot failed or was cancelled.")
                    return
                self.ss_status.config(text="Processing with AI...")
                explanation = self.get_ai_explanation(PROMPT_SCREENSHOT, image_path=SCREENSHOT_PATH)
                if explanation:
                    html_output = self.format_as_html(explanation)
                    self.create_and_show_html(html_output)
                    self.ss_status.config(text="Done! Result opened in browser.")
                else:
                    self.ss_status.config(text="AI explanation failed.")
            except Exception as e:
                self.ss_status.config(text=f"Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def create_audio_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Audio")
        label = ttk.Label(tab, text="AI Audio Helper", font=("Arial", 14, "bold"))
        label.pack(pady=(18, 8))
        desc = ttk.Label(tab, text="Record system audio and get an AI analysis.")
        desc.pack(pady=(0, 10))
        self.audio_status = ttk.Label(tab, text="Ready.")
        self.audio_status.pack(pady=(0, 10))
        self.audio_record_btn = ttk.Button(tab, text="Start Recording", command=self.toggle_audio_recording)
        self.audio_record_btn.pack(pady=(0, 10))
        self.audio_recording = False
        self.audio_proc = None

    def toggle_audio_recording(self):
        if not self.audio_recording:
            self.start_audio_recording()
        else:
            self.stop_audio_recording()

    def start_audio_recording(self):
        self.audio_status.config(text="Recording system audio...")
        cmd = [
            "ffmpeg", "-y",
            "-f", "pulse",
            "-i", "@DEFAULT_MONITOR@",
            "-ac", "2",
            "-ar", "44100",
            "-c:a", "pcm_s16le",
            str(AUDIO_PATH)
        ]
        self.audio_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.audio_recording = True
        self.audio_record_btn.config(text="Stop Recording")

    def stop_audio_recording(self):
        if self.audio_proc:
            self.audio_proc.terminate()
            self.audio_proc.wait(timeout=5)
        self.audio_recording = False
        self.audio_record_btn.config(text="Processing...", state="disabled")
        self.audio_status.config(text="Processing audio with AI...")
        def worker():
            try:
                if not AUDIO_PATH.exists() or AUDIO_PATH.stat().st_size == 0:
                    self.audio_status.config(text="No audio recorded.")
                    self.audio_record_btn.config(text="Start Recording", state="normal")
                    return
                explanation = self.get_ai_explanation(PROMPT_AUDIO, audio_path=AUDIO_PATH)
                if explanation:
                    html_output = self.format_as_html(explanation)
                    self.create_and_show_html(html_output)
                    self.audio_status.config(text="Done! Result opened in browser.")
                else:
                    self.audio_status.config(text="AI explanation failed.")
                self.audio_record_btn.config(text="Start Recording", state="normal")
            except Exception as e:
                self.audio_status.config(text=f"Error: {e}")
                self.audio_record_btn.config(text="Start Recording", state="normal")
        threading.Thread(target=worker, daemon=True).start()

    def create_video_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Video")
        label = ttk.Label(tab, text="AI Video Helper", font=("Arial", 14, "bold"))
        label.pack(pady=(18, 8))
        desc = ttk.Label(tab, text="Record screen video with audio and get an AI analysis.")
        desc.pack(pady=(0, 10))
        self.video_status = ttk.Label(tab, text="Ready.")
        self.video_status.pack(pady=(0, 10))
        self.video_record_btn = ttk.Button(tab, text="Start Recording", command=self.toggle_video_recording)
        self.video_record_btn.pack(pady=(0, 10))
        self.video_recording = False
        self.video_proc = None

    def toggle_video_recording(self):
        if not self.video_recording:
            self.start_video_recording()
        else:
            self.stop_video_recording()

    def start_video_recording(self):
        self.video_status.config(text="Recording screen video...")
        # Use 1920x1080 as fallback, or try to get real resolution
        resolution = "1920x1080"
        try:
            import Xlib.display
            display = Xlib.display.Display()
            screen = display.screen()
            width = screen.width_in_pixels
            height = screen.height_in_pixels
            resolution = f"{width}x{height}"
        except Exception:
            pass
        cmd = [
            "ffmpeg", "-y",
            "-video_size", resolution,
            "-framerate", "25",
            "-f", "x11grab",
            "-i", os.environ.get("DISPLAY", ":0.0"),
            "-f", "pulse",
            "-i", "@DEFAULT_MONITOR@",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "128k",
            str(VIDEO_PATH)
        ]
        self.video_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.video_recording = True
        self.video_record_btn.config(text="Stop Recording")

    def stop_video_recording(self):
        if self.video_proc:
            self.video_proc.terminate()
            self.video_proc.wait(timeout=5)
        self.video_recording = False
        self.video_record_btn.config(text="Processing...", state="disabled")
        self.video_status.config(text="Processing video with AI...")
        def worker():
            try:
                if not VIDEO_PATH.exists() or VIDEO_PATH.stat().st_size == 0:
                    self.video_status.config(text="No video recorded.")
                    self.video_record_btn.config(text="Start Recording", state="normal")
                    return
                explanation = self.get_ai_explanation(PROMPT_VIDEO, video_path=VIDEO_PATH)
                if explanation:
                    html_output = self.format_as_html(explanation)
                    self.create_and_show_html(html_output)
                    self.video_status.config(text="Done! Result opened in browser.")
                else:
                    self.video_status.config(text="AI explanation failed.")
                self.video_record_btn.config(text="Start Recording", state="normal")
            except Exception as e:
                self.video_status.config(text=f"Error: {e}")
                self.video_record_btn.config(text="Start Recording", state="normal")
        threading.Thread(target=worker, daemon=True).start()

    def create_text_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Text")
        label = ttk.Label(tab, text="AI Text Helper", font=("Arial", 14, "bold"))
        label.pack(pady=(18, 8))
        desc = ttk.Label(tab, text="Paste text/code or error message for AI analysis.")
        desc.pack(pady=(0, 10))
        # Use a frame with grid layout for better control
        text_frame = ttk.Frame(tab)
        text_frame.pack(fill=tk.BOTH, expand=True)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        self.text_input = scrolledtext.ScrolledText(text_frame, width=60, height=8, font=("Arial", 11))
        self.text_input.grid(row=0, column=0, sticky="nsew", padx=4, pady=(0, 10))
        self.text_status = ttk.Label(text_frame, text="Ready.")
        self.text_status.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 10))
        btn = ttk.Button(text_frame, text="Analyze Text", command=self.analyze_text)
        btn.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 10))

    def analyze_text(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            self.text_status.config(text="Please enter some text.")
            return
        self.text_status.config(text="Processing with AI...")
        def worker():
            explanation = self.get_ai_explanation(PROMPT_TEXT, text=text)
            if explanation:
                html_output = self.format_as_html(explanation)
                self.create_and_show_html(html_output)
                self.text_status.config(text="Done! Result opened in browser.")
            else:
                self.text_status.config(text="AI explanation failed.")
        threading.Thread(target=worker, daemon=True).start()

    def get_ai_explanation(self, prompt, image_path=None, audio_path=None, video_path=None, text=None):
        try:
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return None
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            if image_path:
                img = Image.open(image_path)
                response = model.generate_content([prompt, img])
            elif audio_path:
                audio_file = genai.upload_file(str(audio_path))
                response = model.generate_content([prompt, audio_file])
            elif video_path:
                video_file = genai.upload_file(str(video_path))
                # Wait for file to become ACTIVE (up to 2 minutes)
                file_id = video_file.name if hasattr(video_file, 'name') else video_file
                import time
                max_wait = 120
                waited = 0
                while waited < max_wait:
                    file_status = genai.get_file(file_id)
                    state = getattr(file_status, 'state', None)
                    if state == 'ACTIVE':
                        break
                    time.sleep(2)
                    waited += 2
                else:
                    return None
                response = model.generate_content([prompt, video_file])
            elif text:
                response = model.generate_content([prompt, text])
            else:
                return None
            return response.text
        except Exception as e:
            return None
        finally:
            for p in [AUDIO_PATH, VIDEO_PATH, SCREENSHOT_PATH]:
                if p.exists():
                    try:
                        os.remove(p)
                    except:
                        pass

    def format_as_html(self, text: str) -> str:
        html_fragment = markdown.markdown(
            text, extensions=['fenced_code', 'codehilite']
        )
        formatter = HtmlFormatter(style='default', full=True, cssclass="codehilite")
        css_styles = formatter.get_style_defs()
        full_html = f"""
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"UTF-8\">
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
            <title>AI Helper Results</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
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

    def create_and_show_html(self, html_content: str):
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                filepath = f.name
            webbrowser.open_new_tab(f'file://{os.path.realpath(filepath)}')
        except Exception:
            pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    AIHelperSuite().run()
