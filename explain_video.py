#!/usr/bin/env python3

import os
import sys
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
import markdown
from pygments.formatters import HtmlFormatter
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

PROMPT = "Analyze this video recording and provide a detailed explanation of what is happening. If possible, answer any questions or errors shown in the video and provide a solution in typescript."
VIDEO_PATH = Path.home() / "temp_video_recording.webm"

class VideoRecorderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Video Helper")
        self.root.geometry("620x420")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.eval('tk::PlaceWindow . center')
        self.is_recording = False
        self.recording_process = None
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        title_label = ttk.Label(main_frame, text="AI Video Helper", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        self.status_label = ttk.Label(main_frame, text="Ready to record screen video")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(main_frame, text="Resolution (e.g. 1920x1080 or 1280x720):").grid(row=2, column=0, sticky=tk.W)
        self.resolution_var = tk.StringVar(value=self.get_screen_resolution())
        self.resolution_entry = ttk.Entry(main_frame, textvariable=self.resolution_var, width=15)
        self.resolution_entry.grid(row=2, column=1, sticky=tk.E)
        ttk.Label(main_frame, text="Region (x,y,w,h, optional):").grid(row=3, column=0, sticky=tk.W)
        self.region_var = tk.StringVar(value="")
        self.region_entry = ttk.Entry(main_frame, textvariable=self.region_var, width=15)
        self.region_entry.grid(row=3, column=1, sticky=tk.E)
        self.record_button = ttk.Button(main_frame, text="Start Recording", command=self.toggle_recording)
        self.record_button.grid(row=4, column=0, padx=(0, 10), sticky=tk.W)
        self.close_button = ttk.Button(main_frame, text="Close", command=self.close_app)
        self.close_button.grid(row=4, column=1, sticky=tk.E)

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        print("Starting screen video recording...")
        try:
            session_type = os.environ.get("XDG_SESSION_TYPE", "")
            print(f"Detected session type: {session_type}")
            if session_type.lower() == "wayland":
                # Use gdbus for Wayland on GNOME
                video_path = str(VIDEO_PATH)
                dbus_cmd = [
                    "/usr/bin/gdbus", "call",
                    "--session",
                    "--dest", "org.gnome.Shell.Screencast",
                    "--object-path", "/org/gnome/Shell/Screencast",
                    "--method", "org.gnome.Shell.Screencast.Screencast",
                    "--",
                    f"file://{video_path}",
                    "{}"
                ]
                print(f"Running gdbus command: {' '.join(dbus_cmd)}")
                self.recording_process = subprocess.Popen(
                    [
                        "/usr/bin/gdbus", "call",
                        "--session",
                        "--dest", "org.gnome.Shell.Screencast",
                        "--object-path", "/org/gnome/Shell/Screencast",
                        "--method", "org.gnome.Shell.Screencast.Screencast",
                        str(VIDEO_PATH),
                        "[]"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = self.recording_process.communicate()
                if not stdout.decode().startswith("(true,"):
                    print(f"Error starting screencast: {stdout.decode()}", file=sys.stderr)
                    self.status_label.config(text="Error: Could not start screencast")
                    return
            else:
                # X11 fallback (existing ffmpeg logic)
                display_env = os.environ.get("DISPLAY")
                if not display_env:
                    display_env = ":0.0"  # fallback if DISPLAY is not set
                print(f"Using DISPLAY={display_env}")
                resolution = self.resolution_var.get().strip() or self.get_screen_resolution()
                print(f"Using resolution: {resolution}")
                region = self.region_var.get().strip()
                if region:
                    try:
                        x, y, w, h = map(int, region.split(","))
                        grab_input = f"{display_env}+{x},{y}"
                        video_size = f"{w}x{h}"
                    except Exception as e:
                        print(f"Invalid region format: {region}. Error: {e}")
                        self.status_label.config(text="Invalid region format. Use x,y,w,h")
                        return
                else:
                    grab_input = display_env
                    video_size = resolution
                cmd = [
                    "ffmpeg", "-y",
                    "-video_size", video_size,
                    "-framerate", "25",
                    "-f", "x11grab",
                    "-i", grab_input,
                    "-f", "pulse",
                    "-i", "@DEFAULT_MONITOR@",
                    "-c:v", "libx264", "-preset", "ultrafast",
                    "-c:a", "aac", "-b:a", "128k",
                    str(VIDEO_PATH)
                ]
                print(f"Running ffmpeg command: {' '.join(cmd)}")
                self.recording_process = subprocess.Popen(
                    cmd,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
            self.is_recording = True
            self.record_button.config(text="Stop Recording")
            self.status_label.config(text="Recording screen video...")
            print("Video recording started successfully")
        except Exception as e:
            print(f"Error starting video recording: {e}", file=sys.stderr)
            self.status_label.config(text="Error: Could not start video recording")

    def stop_recording(self):
        print("Stopping video recording...")
        try:
            session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
            if session_type == "wayland":
                dbus_cmd = [
                    "/usr/bin/gdbus", "call",
                    "--session",
                    "--dest", "org.gnome.Shell.Screencast",
                    "--object-path", "/org/gnome/Shell/Screencast",
                    "--method", "org.gnome.Shell.Screencast.StopScreencast"
                ]
                subprocess.run(dbus_cmd, check=True)
            elif self.recording_process:
                self.recording_process.terminate()
                self.recording_process.wait(timeout=5)

            self.is_recording = False
            self.record_button.config(text="Processing...", state="disabled")
            self.status_label.config(text="Processing video with AI...")
            threading.Thread(target=self.process_video, daemon=True).start()
        except Exception as e:
            print(f"Error stopping video recording: {e}", file=sys.stderr)
            self.status_label.config(text="Error: Could not stop video recording")
            self.reset_ui()

    def process_video(self):
        try:
            if not VIDEO_PATH.exists() or VIDEO_PATH.stat().st_size == 0:
                print("No video recorded or file is empty.")
                self.root.after(0, lambda: self.status_label.config(text="No video recorded."))
                self.root.after(0, self.reset_ui)
                return

            if VIDEO_PATH.stat().st_size < 10240:  # 10 KB
                print(f"Warning: Video file is very small ({VIDEO_PATH.stat().st_size} bytes). It might be blank.")
                self.root.after(0, lambda: self.status_label.config(text="Warning: Video file is very small."))

            # Convert webm to mp4
            mp4_path = VIDEO_PATH.with_suffix(".mp4")
            ffmpeg_cmd = [
                "/usr/bin/ffmpeg", "-y",
                "-i", str(VIDEO_PATH),
                str(mp4_path)
            ]
            subprocess.run(ffmpeg_cmd, check=True)

            explanation = self.upload_video_and_get_explanation(mp4_path)
            if explanation:
                html_output = self.format_as_html(explanation)
                self.create_and_show_html(html_output)
                self.root.after(0, lambda: self.status_label.config(text="Results opened in browser."))
            else:
                self.root.after(0, lambda: self.status_label.config(text="Failed to get AI explanation."))
        except Exception as e:
            print(f"Error processing video: {e}", file=sys.stderr)
            self.root.after(0, lambda: self.status_label.config(text="Error processing video."))
        finally:
            self.root.after(0, self.reset_ui)

    def upload_video_and_get_explanation(self, video_path):
        print("Uploading video and getting explanation...")
        try:
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("FATAL: GOOGLE_API_KEY not found in .env file.", file=sys.stderr)
                return None
            genai.configure(api_key=api_key)
            
            self.root.after(0, lambda: self.status_label.config(text="Uploading video..."))
            print(f"Uploading file: {video_path} (size: {video_path.stat().st_size} bytes)")
            video_file = genai.upload_file(path=str(video_path))
            
            self.root.after(0, lambda: self.status_label.config(text="Waiting for video to be ready..."))
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                print(f"FATAL: Video processing failed: {video_file.state.name}", file=sys.stderr)
                self.root.after(0, lambda: self.status_label.config(text="Video processing failed."))
                return None

            self.root.after(0, lambda: self.status_label.config(text="Generating explanation..."))
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            response = model.generate_content([PROMPT, video_file])
            
            # Clean up the uploaded file
            genai.delete_file(video_file.name)
            
            return response.text
        except Exception as e:
            print(f"FATAL: Error during AI explanation: {e}", file=sys.stderr)
            self.root.after(0, lambda: self.status_label.config(text="Error during AI explanation."))
            return None
        finally:
            if VIDEO_PATH.exists():
                print(f"Video saved at: {VIDEO_PATH}")
        

    def reset_ui(self):
        self.record_button.config(text="Start Recording", state="normal")
        self.status_label.config(text="Ready to record screen video")

    def get_screen_resolution(self):
        try:
            import Xlib.display
            display = Xlib.display.Display()
            screen = display.screen()
            width = screen.width_in_pixels
            height = screen.height_in_pixels
            return f"{width}x{height}"
        except Exception:
            return "1920x1080"  # fallback

    

    def format_as_html(self, text: str) -> str:
        print("Formatting response as HTML...")
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
            <title>AI Video Analysis Results</title>
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
                .video-analysis {{
                    background: #f8f9fa;
                    border-left: 4px solid #007acc;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="video-analysis">
                <h1>🎬 Video Analysis Results</h1>
                {html_fragment}
            </div>
        </body>
        </html>
        """
        return full_html

    def create_and_show_html(self, html_content: str):
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                filepath = f.name
                print(f"Temporary HTML file created at: {filepath}")
            webbrowser.open_new_tab(f'file://{os.path.realpath(filepath)}')
        except Exception as e:
            print(f"FATAL: Could not create or open the HTML file. Error: {e}", file=sys.stderr)

    def close_app(self):
        if self.is_recording and self.recording_process:
            self.recording_process.terminate()
        if VIDEO_PATH.exists():
            try:
                os.remove(VIDEO_PATH)
            except:
                pass
        self.root.destroy()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.root.mainloop()

def check_dependencies():
    missing = []
    if not os.path.exists("/usr/bin/gdbus"):
        missing.append("gdbus")
    if not os.path.exists("/usr/bin/ffmpeg"):
        missing.append("ffmpeg")

    if missing:
        print(f"Missing required dependencies: {', '.join(missing)}")
        print("Please install them. For example:")
        if "gdbus" in missing:
            print("  gdbus is part of libglib2.0-bin, which should be installed by default on GNOME.")
        if "ffmpeg" in missing:
            print("  sudo apt-get install ffmpeg")
        return False
    return True

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
    app = VideoRecorderGUI()
    app.run()
