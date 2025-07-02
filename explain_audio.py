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
from tkinter import ttk

# --- USER CONFIGURATION ---
PROMPT = "Analyze this audio recording and provide a detailed answers of questions you hear and if possible provide a solution in typescript."

# --- SCRIPT CONFIGURATION ---
AUDIO_PATH = Path.home() / "temp_audio_recording.wav"

class AudioRecorderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Audio Helper")
        self.root.geometry("300x150")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        self.is_recording = False
        self.recording_process = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="AI Audio Helper", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready to record system audio")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Record button
        self.record_button = ttk.Button(main_frame, text="Start Recording", command=self.toggle_recording)
        self.record_button.grid(row=2, column=0, padx=(0, 10), sticky=tk.W)
        
        # Close button
        self.close_button = ttk.Button(main_frame, text="Close", command=self.close_app)
        self.close_button.grid(row=2, column=1, sticky=tk.E)
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Start recording system audio using PulseAudio/PipeWire"""
        print("Starting system audio recording...")
        try:
            # Use ffmpeg to record from the monitor source (system audio output)
            # This captures what's being played through the speakers
            cmd = [
                "ffmpeg", "-y",  # -y to overwrite existing file
                "-f", "pulse",
                "-i", "@DEFAULT_MONITOR@",  # Use default monitor source (more reliable)
                "-ac", "2",  # Stereo
                "-ar", "44100",  # Sample rate
                "-c:a", "pcm_s16le",  # Audio codec
                str(AUDIO_PATH)
            ]
            
            self.recording_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            self.is_recording = True
            self.record_button.config(text="Stop Recording")
            self.status_label.config(text="Recording system audio...")
            print("Recording started successfully")
            
        except Exception as e:
            print(f"Error starting recording: {e}", file=sys.stderr)
            self.status_label.config(text="Error: Could not start recording")
            
    def stop_recording(self):
        """Stop recording and process the audio"""
        print("Stopping recording...")
        try:
            if self.recording_process:
                self.recording_process.terminate()
                self.recording_process.wait(timeout=5)
                
            self.is_recording = False
            self.record_button.config(text="Processing...", state="disabled")
            self.status_label.config(text="Processing audio with AI...")
            
            # Process the audio in a separate thread to avoid blocking the UI
            threading.Thread(target=self.process_audio, daemon=True).start()
            
        except Exception as e:
            print(f"Error stopping recording: {e}", file=sys.stderr)
            self.status_label.config(text="Error: Could not stop recording")
            self.reset_ui()
            
    def process_audio(self):
        """Send audio to AI and display results"""
        try:
            if not AUDIO_PATH.exists() or AUDIO_PATH.stat().st_size == 0:
                print("No audio recorded or file is empty")
                self.root.after(0, lambda: self.status_label.config(text="No audio recorded"))
                self.root.after(0, self.reset_ui)
                return
                
            explanation = self.get_ai_explanation()
            if explanation:
                html_output = self.format_as_html(explanation)
                self.create_and_show_html(html_output)
                self.root.after(0, lambda: self.status_label.config(text="Results opened in browser"))
            else:
                self.root.after(0, lambda: self.status_label.config(text="Failed to get AI response"))
                
        except Exception as e:
            print(f"Error processing audio: {e}", file=sys.stderr)
            self.root.after(0, lambda: self.status_label.config(text="Error processing audio"))
        finally:
            self.root.after(0, self.reset_ui)
            
    def reset_ui(self):
        """Reset UI to initial state"""
        self.record_button.config(text="Start Recording", state="normal")
        self.status_label.config(text="Ready to record system audio")
        
    def get_ai_explanation(self):
        """Send the audio file to the Gemini API and return the explanation."""
        print("Sending audio to AI for analysis...")
        try:
            load_dotenv()
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("FATAL: GOOGLE_API_KEY not found in .env file.", file=sys.stderr)
                return None
            
            genai.configure(api_key=api_key)
            
            # Upload the audio file
            audio_file = genai.upload_file(str(AUDIO_PATH))
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content([PROMPT, audio_file])
            
            print("AI response received.")
            return response.text
            
        except Exception as e:
            print(f"FATAL: Error contacting AI model. Error: {e}", file=sys.stderr)
            return None
        finally:
            # Clean up the audio file
            if AUDIO_PATH.exists():
                try:
                    os.remove(AUDIO_PATH)
                except:
                    pass
                    
    def format_as_html(self, text: str) -> str:
        """Convert the AI's markdown response into a full HTML document with syntax highlighting."""
        print("Formatting response as HTML...")
        html_fragment = markdown.markdown(
            text, extensions=['fenced_code', 'codehilite']
        )

        formatter = HtmlFormatter(style='default', full=True, cssclass="codehilite")
        css_styles = formatter.get_style_defs()
        
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Audio Analysis Results</title>
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
                .audio-analysis {{
                    background: #f8f9fa;
                    border-left: 4px solid #007acc;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="audio-analysis">
                <h1>🎵 Audio Analysis Results</h1>
                {html_fragment}
            </div>
        </body>
        </html>
        """
        return full_html

    def create_and_show_html(self, html_content: str):
        """Save content to a temporary HTML file and open it in a new browser tab."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                filepath = f.name
                print(f"Temporary HTML file created at: {filepath}")

            webbrowser.open_new_tab(f'file://{os.path.realpath(filepath)}')

        except Exception as e:
            print(f"FATAL: Could not create or open the HTML file. Error: {e}", file=sys.stderr)
            
    def close_app(self):
        """Clean up and close the application"""
        if self.is_recording and self.recording_process:
            self.recording_process.terminate()
        if AUDIO_PATH.exists():
            try:
                os.remove(AUDIO_PATH)
            except:
                pass
        self.root.destroy()
        
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self.root.mainloop()

def check_dependencies():
    """Check if required system dependencies are available"""
    required_commands = {"ffmpeg": "-version", "pactl": "--version"}
    missing = []
    
    for cmd, version_flag in required_commands.items():
        try:
            result = subprocess.run([cmd, version_flag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if result.returncode != 0:
                missing.append(cmd)
        except FileNotFoundError:
            missing.append(cmd)
    
    if missing:
        print(f"Missing required dependencies: {', '.join(missing)}")
        print("Please install them using:")
        if "ffmpeg" in missing:
            print("  sudo apt-get install ffmpeg")
        if "pactl" in missing:
            print("  sudo apt-get install pulseaudio-utils")
        return False
    return True

if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
        
    app = AudioRecorderGUI()
    app.run()
