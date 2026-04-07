"""
OHW - Oral History Workflow
A Flet UI app designed to streamline the oral history recording and ingest workflow
for Digital.Grinnell, including WAV-to-MP3 conversion and future processing steps.
"""

import flet as ft
import os
import logging
import json
import subprocess
import shutil
import warnings
import re
from datetime import datetime
from pathlib import Path

# DOCX handling imports
try:
    from docx import Document
    from docx2pdf import convert as docx2pdf_convert
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_LEFT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Transcription imports (openai-whisper)
try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
    # Suppress FP16 warning if no GPU
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Transcription libraries not available. Install with: pip install openai-whisper torch torchaudio")

# Configure logging
DATA_DIR = Path.home() / "OHW-data"
os.makedirs(DATA_DIR / "logfiles", exist_ok=True)
log_filename = DATA_DIR / "logfiles" / f"ohw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

# Reduce Flet's logging verbosity
logging.getLogger("flet").setLevel(logging.WARNING)
logging.getLogger("flet_core").setLevel(logging.WARNING)
logging.getLogger("flet_desktop").setLevel(logging.WARNING)

# Persistent storage file
PERSISTENCE_FILE = DATA_DIR / "persistent.json"


class PersistentStorage:
    """Handle persistent storage of UI state and function usage."""

    def __init__(self):
        self.data = self.load()

    def load(self) -> dict:
        """Load persistent data from file."""
        try:
            if os.path.exists(PERSISTENCE_FILE):
                with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Loaded persistent data from {PERSISTENCE_FILE}")
                return data
        except Exception as e:
            logger.warning(f"Could not load persistent data: {str(e)}")

        return {
            "ui_state": {
                "last_wav_dir": "",
                "last_mp3_dir": "",
                "last_input_dir": "",
                "window_left": None,
                "window_top": None,
            },
            "function_usage": {},
            "speaker_names": ["", "", "", "", ""],
        }

    def save(self):
        """Save persistent data to file."""
        try:
            with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved persistent data to {PERSISTENCE_FILE}")
        except Exception as e:
            logger.error(f"Could not save persistent data: {str(e)}")

    def set_ui_state(self, field: str, value: str):
        """Update UI state field."""
        self.data["ui_state"][field] = value
        self.save()

    def get_ui_state(self, field: str, default: str = "") -> str:
        """Get UI state field."""
        return self.data["ui_state"].get(field, default)

    def record_function_usage(self, function_name: str):
        """Record that a function was used."""
        if function_name not in self.data["function_usage"]:
            self.data["function_usage"][function_name] = {"count": 0}

        self.data["function_usage"][function_name]["last_used"] = datetime.now().isoformat()
        self.data["function_usage"][function_name]["count"] = (
            self.data["function_usage"][function_name].get("count", 0) + 1
        )
        self.save()

    def get_function_usage(self, function_name: str) -> dict:
        """Get usage stats for a function."""
        return self.data["function_usage"].get(
            function_name, {"last_used": None, "count": 0}
        )

    def get_all_function_usage(self) -> dict:
        """Get all function usage stats."""
        return self.data["function_usage"]

    def get_speaker_names(self) -> list:
        """Get the list of speaker names."""
        return self.data.get("speaker_names", ["", "", "", "", ""])

    def set_speaker_names(self, names: list):
        """Save the list of speaker names."""
        self.data["speaker_names"] = names
        self.save()


def check_ffmpeg() -> bool:
    """Return True if ffmpeg is available on PATH."""
    return shutil.which("ffmpeg") is not None


def convert_wav_to_mp3(
    wav_path: Path,
    mp3_path: Path,
    quality: int = 2,
    sample_rate: int = 44100,
) -> tuple[bool, str]:
    """
    Convert a WAV file to MP3 using ffmpeg.

    Args:
        wav_path: Path to the source WAV file.
        mp3_path: Destination path for the MP3 file.
        quality:  VBR quality level (0=best, 9=worst; 2 approx. 190 kbps).
        sample_rate: Output sample rate in Hz.

    Returns:
        (success, message)
    """
    if not check_ffmpeg():
        return False, (
            "ffmpeg is not installed. Please install it:\n"
            "  • macOS:  brew install ffmpeg\n"
            "  • Linux:  sudo apt install ffmpeg\n"
            "  • Windows: https://ffmpeg.org/download.html"
        )

    if not wav_path.exists():
        return False, f"Source file not found: {wav_path}"

    if mp3_path.exists():
        return False, f"Output file already exists: {mp3_path}"

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", str(wav_path),
                "-codec:a", "libmp3lame",
                "-q:a", str(quality),
                "-ar", str(sample_rate),
                str(mp3_path),
                "-hide_banner",
                "-loglevel", "error",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode == 0 and mp3_path.exists():
            wav_mb = wav_path.stat().st_size / (1024 * 1024)
            mp3_mb = mp3_path.stat().st_size / (1024 * 1024)
            return True, (
                f"✅ Conversion successful!\n\n"
                f"Created: {mp3_path.name}\n"
                f"Location: {mp3_path.parent}\n\n"
                f"WAV: {wav_mb:.1f} MB  →  MP3: {mp3_mb:.1f} MB"
            )

        error_msg = result.stderr.strip() if result.stderr else "Unknown ffmpeg error"
        return False, f"❌ ffmpeg error:\n\n{error_msg}"

    except subprocess.TimeoutExpired:
        return False, "❌ Conversion timed out after 10 minutes."
    except Exception as exc:
        return False, f"❌ Unexpected error: {exc}"


def main(page: ft.Page):
    page.title = "OHW - Oral History Workflow"
    page.padding = 20
    page.window.width = 1400
    page.window.height = 950
    page.scroll = ft.ScrollMode.AUTO

    storage = PersistentStorage()
    logger.info("OHW application started")

    # ------------------------------------------------------------------ helpers

    def add_log_message(text: str):
        """Prepend a timestamped line to the log output field."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        existing = log_output.value or ""
        log_output.value = f"[{timestamp}] {text}\n{existing}"
        page.update()

    def update_status(message: str, is_error: bool = False):
        """Update the status text widget."""
        status_text.value = message
        status_text.color = ft.Colors.RED_600 if is_error else ft.Colors.GREEN_700
        page.update()

    # ------------------------------------------------------------------ widgets

    status_text = ft.Text(
        "Ready",
        size=14,
        color=ft.Colors.GREEN_700,
        italic=True,
    )

    log_output = ft.TextField(
        multiline=True,
        read_only=True,
        min_lines=8,
        max_lines=12,
        text_size=12,
        border_color=ft.Colors.GREY_400,
        bgcolor=ft.Colors.GREY_100,
        value="",
    )

    # -------------------------------------------------------- Input state
    selected_file: Path | None = None
    current_directory: Path | None = None
    audio_files: list[Path] = []
    output_directory: Path | None = None  # Directory for current file's outputs
    current_epoch: int | None = None  # Epoch timestamp for current file

    # Directory picker
    directory_picker = ft.FilePicker()
    page.overlay.append(directory_picker)

    # Input directory text field
    input_directory_field = ft.TextField(
        label="Input Directory",
        hint_text="Select a directory containing WAV/MP3 files",
        width=600,
        read_only=True,
        value=""
    )

    # File selection dropdown
    file_selection_dropdown = ft.Dropdown(
        label="Select Audio File",
        hint_text="Click 'List WAV and MP3 Files' to populate",
        width=600,
        options=[],
    )

    # Initialize with last used directory
    last_dir = storage.get_ui_state("last_input_dir")
    if last_dir and os.path.isdir(last_dir):
        current_directory = Path(last_dir)
        input_directory_field.value = str(current_directory)

    # -------------------------------------------------------- input handlers

    def on_directory_picked(e: ft.FilePickerResultEvent):
        """Called when user selects a directory."""
        nonlocal current_directory, audio_files
        if not e.path:
            add_log_message("Directory selection cancelled")
            return

        current_directory = Path(e.path)
        input_directory_field.value = str(current_directory)
        storage.set_ui_state("last_input_dir", str(current_directory))
        
        # Clear file list
        audio_files = []
        file_selection_dropdown.options = []
        file_selection_dropdown.value = None
        
        add_log_message(f"Directory selected: {current_directory}")
        update_status(f"Directory: {current_directory.name}")
        page.update()

    directory_picker.on_result = on_directory_picked

    def on_pick_directory_click(e):
        """Open directory picker."""
        initial_dir = storage.get_ui_state("last_input_dir") or str(Path.home())
        directory_picker.get_directory_path(
            dialog_title="Select directory containing audio files",
            initial_directory=initial_dir if os.path.isdir(initial_dir) else None,
        )

    def on_list_files_click(e):
        """List all WAV and MP3 files in the selected directory and subdirectories."""
        nonlocal audio_files
        
        if not current_directory or not current_directory.exists():
            update_status("Please select a directory first", is_error=True)
            add_log_message("No directory selected")
            return

        try:
            # Find all WAV and MP3 files recursively in subdirectories
            audio_files = []
            for ext in ["**/*.wav", "**/*.WAV", "**/*.mp3", "**/*.MP3"]:
                audio_files.extend(current_directory.glob(ext))
            
            # Sort by relative path
            audio_files.sort(key=lambda p: str(p.relative_to(current_directory)).lower())

            if not audio_files:
                update_status("No WAV or MP3 files found in directory or subdirectories", is_error=True)
                add_log_message(f"No audio files found in {current_directory} or its subdirectories")
                file_selection_dropdown.options = []
                file_selection_dropdown.value = None
                page.update()
                return

            # Populate dropdown with relative paths for better visibility
            file_selection_dropdown.options = [
                ft.dropdown.Option(
                    key=str(f), 
                    text=str(f.relative_to(current_directory))
                ) for f in audio_files
            ]
            file_selection_dropdown.value = None
            
            add_log_message(f"Found {len(audio_files)} audio file(s) in {current_directory.name} and subdirectories")
            update_status(f"Found {len(audio_files)} audio file(s)")
            page.update()

        except Exception as ex:
            update_status(f"Error listing files: {str(ex)}", is_error=True)
            add_log_message(f"Error listing files: {str(ex)}")

    def on_file_selected(e):
        """Called when user selects a file from dropdown."""
        nonlocal selected_file, output_directory, current_epoch
        
        if e.control.value:
            selected_file = Path(e.control.value)
            
            # Extract basename (filename without extension)
            basename = selected_file.stem
            
            # Search for existing directory with this basename
            import time
            import re
            
            # First check if the file is already in an output directory
            # Output directories match pattern: * - dg_<epoch>
            parent_dir = selected_file.parent
            if re.search(r' - dg_\d+$', parent_dir.name):
                # File is already in an output directory - reuse it
                output_directory = parent_dir
                match = re.search(r'dg_(\d+)$', parent_dir.name)
                if match:
                    current_epoch = int(match.group(1))
                    add_log_message(f"File selected: {selected_file.name}")
                    add_log_message(f"Using existing output directory: {output_directory.name}")
                    update_status(f"Selected: {selected_file.name} → {output_directory.name}")
                    logger.info(f"Reusing file's parent directory: {output_directory}")
                    return
            
            # File is not in an output directory, search for one based on basename
            existing_dirs = list(DATA_DIR.glob(f"{basename} - dg_*"))
            
            if existing_dirs:
                # Reuse the first matching directory
                output_directory = existing_dirs[0]
                
                # Extract epoch from directory name using regex
                # Pattern: <basename> - dg_<epoch>
                match = re.search(r'dg_(\d+)$', output_directory.name)
                if match:
                    current_epoch = int(match.group(1))
                    add_log_message(f"File selected: {selected_file.name}")
                    add_log_message(f"Reusing existing output directory: {output_directory.name}")
                    update_status(f"Selected: {selected_file.name} → {output_directory.name}")
                    logger.info(f"Reusing output directory: {output_directory}")
                else:
                    # Shouldn't happen, but fallback to creating new
                    add_log_message("Warning: Could not extract epoch from existing directory")
                    epoch = int(time.time())
                    current_epoch = epoch
                    dirname = f"{basename} - dg_{epoch}"
                    output_directory = DATA_DIR / dirname
                    try:
                        output_directory.mkdir(parents=True, exist_ok=True)
                        add_log_message(f"File selected: {selected_file.name}")
                        add_log_message(f"Created output directory: {output_directory}")
                        update_status(f"Selected: {selected_file.name} → {dirname}")
                        logger.info(f"Created output directory: {output_directory}")
                    except Exception as ex:
                        add_log_message(f"Error creating output directory: {str(ex)}")
                        update_status(f"Error creating output directory: {str(ex)}", is_error=True)
                        logger.error(f"Failed to create output directory: {str(ex)}")
                        selected_file = None
                        output_directory = None
                        current_epoch = None
            else:
                # No existing directory found, create a new one
                epoch = int(time.time())
                current_epoch = epoch
                dirname = f"{basename} - dg_{epoch}"
                output_directory = DATA_DIR / dirname
                
                try:
                    output_directory.mkdir(parents=True, exist_ok=True)
                    add_log_message(f"File selected: {selected_file.name}")
                    add_log_message(f"Created new output directory: {output_directory}")
                    update_status(f"Selected: {selected_file.name} → {dirname}")
                    logger.info(f"Created output directory: {output_directory}")
                except Exception as ex:
                    add_log_message(f"Error creating output directory: {str(ex)}")
                    update_status(f"Error creating output directory: {str(ex)}", is_error=True)
                    logger.error(f"Failed to create output directory: {str(ex)}")
                    selected_file = None
                    output_directory = None
                    current_epoch = None
        else:
            selected_file = None
            output_directory = None
            current_epoch = None

    file_selection_dropdown.on_change = on_file_selected

    # -------------------------------------------------------- function handlers

    def on_function_1_wav_to_mp3(e):
        """Execute Function 1: WAV to MP3 Conversion"""
        nonlocal selected_file, output_directory, current_epoch
        
        if not check_ffmpeg():
            update_status(
                "⚠️  ffmpeg not found — install it before converting WAV files.",
                is_error=True,
            )
            add_log_message(
                "ffmpeg not installed. Install via: brew install ffmpeg (macOS) "
                "or sudo apt install ffmpeg (Linux)"
            )
            return

        # Check if a file is selected
        if not selected_file:
            update_status("Please select an audio file first", is_error=True)
            add_log_message("No file selected. Use Inputs section to select a file.")
            return

        # Check if output directory exists
        if not output_directory or not output_directory.exists():
            update_status("Output directory not found. Please reselect the file.", is_error=True)
            add_log_message("Output directory missing. Reselect the file to recreate it.")
            return

        # Check if epoch is available
        if not current_epoch:
            update_status("Epoch timestamp not found. Please reselect the file.", is_error=True)
            add_log_message("Epoch timestamp missing. Reselect the file to regenerate it.")
            return

        # Only convert WAV files
        if selected_file.suffix.lower() != ".wav":
            update_status(
                f"Cannot convert {selected_file.suffix} file. Please select a WAV file.",
                is_error=True,
            )
            add_log_message(f"Skipped: {selected_file.name} is not a WAV file")
            return

        # Define standardized filenames using epoch
        wav_filename = f"dg_{current_epoch}.wav"
        mp3_filename = f"dg_{current_epoch}.mp3"
        wav_copy_path = output_directory / wav_filename
        mp3_path = output_directory / mp3_filename

        # Step 1: Copy WAV file to output directory if it doesn't already exist
        if wav_copy_path.exists():
            add_log_message(f"WAV file already exists in output directory: {wav_filename}")
        else:
            try:
                add_log_message(f"Copying WAV file to output directory: {wav_filename}")
                update_status(f"Copying {selected_file.name} to output directory...")
                page.update()
                
                shutil.copy2(selected_file, wav_copy_path)
                
                wav_size_mb = wav_copy_path.stat().st_size / (1024 * 1024)
                add_log_message(f"✅ WAV file copied: {wav_filename} ({wav_size_mb:.1f} MB)")
            except Exception as ex:
                update_status(f"Error copying WAV file: {str(ex)}", is_error=True)
                add_log_message(f"❌ Failed to copy WAV file: {str(ex)}")
                logger.error(f"WAV copy failed: {str(ex)}")
                return

        # Step 2: Check if MP3 already exists
        if mp3_path.exists():
            update_status(
                f"⚠️  MP3 already exists: {mp3_filename} — skipping conversion.",
                is_error=True,
            )
            add_log_message(f"Skipped: {mp3_filename} already exists in {output_directory.name}")
            return

        # Step 3: Convert the copied WAV file to MP3
        storage.record_function_usage("function_1_wav_to_mp3")
        update_status(f"Converting {wav_filename} to MP3 …")
        add_log_message(f"Starting conversion: {wav_filename} → {mp3_filename}")
        page.update()

        success, message = convert_wav_to_mp3(wav_copy_path, mp3_path)

        if success:
            add_log_message(f"✅ Conversion complete: {mp3_filename}")
            add_log_message(f"✅ Output location: {output_directory}")
        else:
            add_log_message(f"❌ Conversion failed: {message}")

        update_status(message.splitlines()[0], is_error=not success)
        page.update()

    def on_function_2a_transcribe_whisper(e):
        """Execute Function 2a: Transcribe MP3 using OpenAI Whisper"""
        nonlocal selected_file, output_directory, current_epoch
        
        # Check if Whisper is available
        if not WHISPER_AVAILABLE:
            update_status(
                "⚠️  Whisper not installed. Install dependencies first.",
                is_error=True,
            )
            add_log_message(
                "Whisper libraries not available. Install with:\n"
                "pip install openai-whisper python-docx torch torchaudio"
            )
            return

        # Check if a file is selected
        if not selected_file:
            update_status("Please select an audio file first", is_error=True)
            add_log_message("No file selected. Use Inputs section to select a file.")
            return

        # Check if output directory exists
        if not output_directory or not output_directory.exists():
            update_status("Output directory not found. Please reselect the file.", is_error=True)
            add_log_message("Output directory missing. Reselect the file to recreate it.")
            return

        # Check if epoch is available
        if not current_epoch:
            update_status("Epoch timestamp not found. Please reselect the file.", is_error=True)
            add_log_message("Epoch timestamp missing. Reselect the file to regenerate it.")
            return

        # Only transcribe MP3 files
        if selected_file.suffix.lower() != ".mp3":
            update_status(
                f"Cannot transcribe {selected_file.suffix} file. Please select an MP3 file.",
                is_error=True,
            )
            add_log_message(f"Skipped: {selected_file.name} is not an MP3 file")
            return

        # Check if MP3 exists in output directory (it should if converted)
        mp3_filename = f"dg_{current_epoch}.mp3"
        mp3_path = output_directory / mp3_filename
        
        # Use the MP3 from output directory if it exists, otherwise use selected file
        if mp3_path.exists():
            audio_to_transcribe = mp3_path
            add_log_message(f"Using MP3 from output directory: {mp3_filename}")
        else:
            audio_to_transcribe = selected_file
            add_log_message(f"Using selected MP3 file: {selected_file.name}")

        # Define output filenames
        base_name = f"dg_{current_epoch}"
        json_path = output_directory / f"{base_name}_transcript.json"
        
        # Check if transcription already exists
        if json_path.exists():
            update_status(
                f"⚠️  Transcription JSON already exists — skipping.",
                is_error=True,
            )
            add_log_message(f"Skipped: Transcription JSON already exists in {output_directory.name}")
            return

        storage.record_function_usage("function_2a_transcribe_whisper")
        update_status(f"Transcribing {audio_to_transcribe.name} with Whisper ...")
        add_log_message(f"Starting transcription: {audio_to_transcribe.name}")
        page.update()

        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Step 1: Transcribe with OpenAI Whisper (segment-level only)
            add_log_message(f"Loading Whisper model (base, {device})...")
            update_status(f"Loading Whisper model...")
            page.update()
            
            model = whisper.load_model("base", device=device)
            
            add_log_message("Transcribing audio...")
            update_status("Transcribing audio (this may take several minutes)...")
            page.update()
            
            # Custom progress callback to update UI
            import sys
            
            class ProgressCapture:
                def __init__(self):
                    self.last_update = 0
                    self.buffer = []
                    
                def write(self, text):
                    import time
                    # Collect output and update UI periodically
                    if text.strip():
                        self.buffer.append(text.strip())
                        current_time = time.time()
                        if current_time - self.last_update > 1:
                            # Show the most recent meaningful output
                            if self.buffer:
                                display_text = self.buffer[-1]
                                if len(display_text) > 100:
                                    display_text = display_text[:100] + "..."
                                update_status(f"Transcribing: {display_text}")
                                page.update()
                                self.last_update = current_time
                            
                def flush(self):
                    pass
            
            # Redirect stdout temporarily to capture progress
            old_stdout = sys.stdout
            progress_capture = ProgressCapture()
            sys.stdout = progress_capture
            
            try:
                # Transcribe - get segment-level results
                result = model.transcribe(
                    str(audio_to_transcribe),
                    language=None,  # Auto-detect
                    verbose=True,  # Enable progress output
                    word_timestamps=False  # No word-level data
                )
            finally:
                # Restore stdout
                sys.stdout = old_stdout
            
            detected_language = result.get("language", "en")
            add_log_message(f"Language detected: {detected_language}")
            
            # Extract segments
            transcript_segments = []
            for segment in result.get("segments", []):
                transcript_segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"]
                })
            
            add_log_message(f"Transcription complete. {len(transcript_segments)} segments found.")
            
            # Add default speaker label to all segments
            final_segments = []
            for seg in transcript_segments:
                final_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "speaker": "SPEAKER_00"
                })
            
            # Save JSON
            add_log_message("Saving JSON transcript...")
            update_status("Saving transcript JSON...")
            page.update()
            
            output_data = {
                "language": detected_language,
                "segments": final_segments
            }
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            add_log_message(f"✅ Created: {json_path.name}")
            add_log_message(f"✅ Transcription complete! Language: {detected_language}")
            add_log_message(f"✅ Segments: {len(final_segments)}")
            add_log_message(f"✅ Output location: {output_directory}")
            add_log_message("ℹ️  Edit the JSON file to change speaker names from SPEAKER_00, fix spelling, etc.")
            add_log_message("ℹ️  Then use Function 3 to generate TXT and VTT outputs.")
            
            success_msg = f"✅ Transcription complete! {len(final_segments)} segments."
            update_status(success_msg)
            
        except Exception as ex:
            error_msg = f"❌ Transcription failed: {str(ex)}"
            add_log_message(error_msg)
            update_status(error_msg, is_error=True)
            logger.error(f"Transcription error: {str(ex)}")
        
        page.update()

    def on_function_2b_ms_word_online(e):
        """Provide instructions for manual transcription using MS Word Online."""
        nonlocal selected_file, output_directory, current_epoch
        
        if not selected_file:
            update_status("No file selected. Please select a file first.", is_error=True)
            add_log_message("No file selected")
            return

        # Determine which file to use for transcription
        audio_to_transcribe = None
        base_name = f"dg_{current_epoch}" if current_epoch else None
        
        # Priority: use MP3 from output directory if it exists
        if output_directory and base_name:
            mp3_in_output = output_directory / f"{base_name}.mp3"
            if mp3_in_output.exists():
                audio_to_transcribe = mp3_in_output
        
        # Otherwise use selected MP3 file
        if not audio_to_transcribe and selected_file.suffix.lower() == '.mp3':
            audio_to_transcribe = selected_file
        
        if not audio_to_transcribe:
            update_status("⚠️  No MP3 file available. Use Function 1 to convert WAV to MP3 first.", is_error=True)
            add_log_message("No MP3 file found for transcription")
            return

        storage.record_function_usage("function_2b_ms_word_online")
        
        # Create instructions dialog
        expected_docx_name = f"{audio_to_transcribe.stem}.docx"
        expected_json_name = f"dg_{current_epoch}_transcript.json" if current_epoch else f"{audio_to_transcribe.stem}_transcript.json"
        output_path = str(output_directory if output_directory else audio_to_transcribe.parent)
        
        # Get speaker names from UI
        speaker_names = get_speaker_names()
        active_speakers = [name for name in speaker_names if name.strip()]
        
        # Helper function to create copyable text field
        def copyable_field(label, value):
            return ft.Column([
                ft.Text(label, size=12, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(
                        value,
                        size=13,
                        selectable=True,
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=ft.Colors.BLUE_900,
                    padding=8,
                    border_radius=4,
                ),
            ], spacing=3)
        
        # Show instructions in a dialog
        def close_dialog(e):
            dialog.open = False
            page.update()
        
        def on_convert_docx(e):
            """Handle DOCX to JSON conversion."""
            docx_path = Path(output_path) / expected_docx_name
            json_path = Path(output_path) / expected_json_name
            
            if not docx_path.exists():
                update_status(f"DOCX file not found: {docx_path.name}", is_error=True)
                add_log_message(f"❌ DOCX file not found: {docx_path}")
                return
            
            update_status("Converting DOCX to JSON...")
            add_log_message(f"📝 Converting {docx_path.name} to JSON...")
            
            success, message = convert_docx_to_json(docx_path, json_path, speaker_names)
            
            if success:
                update_status(f"✓ {message}")
                add_log_message(f"✓ {message}")
                add_log_message(f"  JSON: {json_path.name}")
                # Close dialog on success
                dialog.open = False
                page.update()
            else:
                update_status(message, is_error=True)
                add_log_message(f"❌ {message}")
        
        dialog = ft.AlertDialog(
            title=ft.Text("📝 MS Word Online Transcription Instructions"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Selected Audio File", size=16, weight=ft.FontWeight.BOLD),
                        copyable_field("Audio Filename:", audio_to_transcribe.name),
                        copyable_field("Audio Location:", str(audio_to_transcribe.parent)),
                        
                        ft.Divider(height=20),
                        
                        ft.Text("Speaker Names (from UI)", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Copy these names when editing transcription in Word:", size=12, italic=True),
                        ft.Column([
                            copyable_field(f"Speaker {i+1}:", name) 
                            for i, name in enumerate(speaker_names) 
                            if name.strip()
                        ] if active_speakers else [
                            ft.Text("No speaker names entered in UI", size=12, italic=True, color=ft.Colors.GREY_600)
                        ], spacing=3),
                        
                        ft.Divider(height=20),
                        
                        ft.Text("STEP 1: Open Microsoft Word Online", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("1. Click link below to open Word Online:"),
                        ft.TextButton(
                            "https://www.office.com/launch/word",
                            url="https://www.office.com/launch/word",
                            style=ft.ButtonStyle(color=ft.Colors.BLUE_700),
                        ),
                        ft.Text("2. Sign in with your Microsoft 365 account (subscription required)"),
                        ft.Text("3. Click 'Blank document'"),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("STEP 2: Set Document Name", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("1. Click on 'Document' at the top of the Word window"),
                        ft.Text("2. Replace it with this name (copy text below):"),
                        copyable_field("Document Name:", audio_to_transcribe.stem),
                        ft.Text("3. Press Enter to confirm"),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("STEP 3: Start Transcription", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("1. Click the 'Home' tab (if not already selected)"),
                        ft.Text("2. Click 'Dictate' dropdown → Select 'Transcribe'"),
                        ft.Text("3. In the Transcribe pane, click 'Upload audio'"),
                        ft.Text("4. Browse to and select your audio file:"),
                        copyable_field("Audio File to Upload:", audio_to_transcribe.name),
                        ft.Text("5. Wait for transcription to complete (may take several minutes)"),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("STEP 4: Review & Edit", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("1. Review the transcription in the Transcribe pane"),
                        ft.Text("2. Edit speaker names (replace 'Speaker 1' with actual names)"),
                        ft.Text("3. Fix any transcription errors"),
                        ft.Text("4. When satisfied, click 'Add to document' at bottom of pane"),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("STEP 5: Save as DOCX", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("1. Click the 'File' menu in Word"),
                        ft.Text("2. Select 'Create a Copy'"),
                        ft.Text("3. Select 'Download a copy'"),
                        ft.Text("4. Click 'Download a copy' to confirm"),
                        ft.Text("5. The file will download to your Downloads folder"),
                        ft.Text("6. IMPORTANT: Move the downloaded DOCX file to this location:", weight=ft.FontWeight.BOLD),
                        copyable_field("Output Directory:", output_path),
                        ft.Text("7. Ensure the filename is exactly:", weight=ft.FontWeight.BOLD),
                        copyable_field("Expected DOCX Filename:", expected_docx_name),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("STEP 6: Convert to JSON", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("After moving the DOCX file to the output directory:"),
                        ft.Container(
                            content=ft.ElevatedButton(
                                "Convert to JSON",
                                icon=ft.Icons.AUTO_FIX_HIGH,
                                on_click=on_convert_docx,
                            ),
                            padding=ft.padding.only(top=10, bottom=10),
                        ),
                        ft.Text(
                            "This will automatically parse the DOCX transcription and create the JSON file.",
                            size=12,
                            italic=True,
                            color=ft.Colors.GREY_700,
                        ),
                        
                        ft.Divider(height=15),
                        
                        ft.Text("STEP 7: Generate Final Outputs", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("After conversion completes, use Function 4 to generate TXT and VTT outputs."),
                        
                        ft.Divider(height=15),
                        
                        ft.Text(
                            "Note: MS Word Online transcription is a Microsoft service. "
                            "This function provides instructions only - the actual transcription happens in your web browser.",
                            size=12,
                            italic=True,
                            color=ft.Colors.GREY_700,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=5,
                ),
                width=700,
                height=600,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(dialog)
        dialog.open = True
        page.update()
        
        add_log_message(f"📝 Displayed MS Word Online instructions for: {audio_to_transcribe.name}")
        update_status(f"Follow the instructions to transcribe with MS Word Online")

    def convert_docx_to_json(docx_path, output_json_path, ui_speaker_names=None):
        """Convert MS Word transcription DOCX to JSON format.
        
        Args:
            docx_path: Path to DOCX file
            output_json_path: Path for output JSON file
            ui_speaker_names: List of speaker names from UI (optional)
        """
        try:
            if not DOCX_AVAILABLE:
                raise ImportError("python-docx library is required. Install it with: pip install python-docx")
            
            # Clean up UI speaker names
            ui_speakers = [name.strip() for name in (ui_speaker_names or []) if name and name.strip()]
            
            # Parse DOCX file
            doc = Document(docx_path)
            
            # DEBUG: Log all paragraph content to understand the format
            add_log_message("📋 DEBUG: Parsing DOCX paragraphs...")
            paragraph_count = 0
            for p in doc.paragraphs:
                if p.text.strip():
                    paragraph_count += 1
                    if paragraph_count <= 10:  # Show first 10 non-empty paragraphs
                        add_log_message(f"  Para {paragraph_count}: {p.text[:100]}")
            add_log_message(f"  Total non-empty paragraphs: {paragraph_count}")
            
            # Extract text and parse timestamps/speakers
            # Word transcription format: timestamp and speaker on one line, text on next line(s)
            # Format: "00:00:00 Speaker Name"
            segments = []
            current_speaker = "SPEAKER_00"
            current_timestamp = None
            current_text = []
            
            # Track unique speakers in order they appear to map to UI names
            docx_speakers_seen = []
            speaker_mapping = {}  # Map DOCX speaker to UI speaker
            
            # Regex pattern for Word's timestamp format: HH:MM:SS Speaker
            timestamp_speaker_pattern = re.compile(r'^(\d{1,2}):(\d{2}):(\d{2})\s+(.+)$')
            
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            
            for i, text in enumerate(paragraphs):
                # Check if this line is a timestamp + speaker line
                match = timestamp_speaker_pattern.match(text)
                
                if match:
                    # Save previous segment if we have collected text
                    if current_timestamp is not None and current_text:
                        # Calculate end time (use next timestamp or add 3 seconds)
                        end_time = current_timestamp + 3.0
                        
                        segments.append({
                            "start": round(current_timestamp, 3),
                            "end": round(end_time, 3),
                            "text": " ".join(current_text),
                            "speaker": current_speaker
                        })
                    
                    # Start new segment
                    hours, minutes, seconds, docx_speaker = match.groups()
                    current_timestamp = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                    
                    # Map DOCX speaker to UI speaker name
                    docx_speaker = docx_speaker.strip()
                    if docx_speaker not in speaker_mapping:
                        # First time seeing this speaker - map to next UI name
                        if docx_speaker not in docx_speakers_seen:
                            docx_speakers_seen.append(docx_speaker)
                        
                        speaker_index = docx_speakers_seen.index(docx_speaker)
                        if ui_speakers and speaker_index < len(ui_speakers):
                            # Use UI speaker name as-is (preserve case and spaces)
                            speaker_mapping[docx_speaker] = ui_speakers[speaker_index]
                        else:
                            # No UI name available, keep DOCX name as-is
                            speaker_mapping[docx_speaker] = docx_speaker
                    
                    current_speaker = speaker_mapping[docx_speaker]
                    current_text = []
                else:
                    # This is text content, add to current segment
                    if text and not text.startswith('Audio file') and not text.startswith('Transcript'):
                        current_text.append(text)
            
            # Don't forget the last segment
            if current_timestamp is not None and current_text:
                segments.append({
                    "start": round(current_timestamp, 3),
                    "end": round(current_timestamp + 3.0, 3),
                    "text": " ".join(current_text),
                    "speaker": current_speaker
                })
            
            # Update end times based on next segment's start time
            for i in range(len(segments) - 1):
                segments[i]["end"] = segments[i + 1]["start"]
            
            # Create JSON in Whisper format
            transcript_data = {
                "language": "en",
                "segments": segments
            }
            
            # Save JSON
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            return True, f"Successfully created JSON with {len(segments)} segments"
            
        except Exception as e:
            return False, f"Conversion failed: {str(e)}"

    def generate_pdf_from_json(json_path, pdf_path, segments):
        """Generate a formatted PDF from JSON transcript segments."""
        try:
            if not PDF_AVAILABLE:
                raise ImportError("reportlab library is required. Install it with: pip install reportlab")
            
            # Derive MP3 filename from JSON path
            # json_path is like: dg_1775499960_transcript.json
            # mp3_filename should be: dg_1775499960.mp3
            json_filename = Path(json_path).name
            mp3_filename = json_filename.replace('_transcript.json', '.mp3')
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Create custom styles
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Normal'],
                fontSize=12,
                textColor='black',
                spaceAfter=6,
                alignment=TA_LEFT,
                fontName='Helvetica-Bold',
            )
            
            filename_style = ParagraphStyle(
                'Filename',
                parent=styles['Normal'],
                fontSize=11,
                textColor='black',
                spaceAfter=12,
                alignment=TA_LEFT,
            )
            
            timestamp_style = ParagraphStyle(
                'Timestamp',
                parent=styles['Normal'],
                fontSize=11,
                textColor='black',
                spaceAfter=4,
                alignment=TA_LEFT,
            )
            
            text_style = ParagraphStyle(
                'Text',
                parent=styles['Normal'],
                fontSize=11,
                textColor='black',
                spaceAfter=12,
                alignment=TA_LEFT,
            )
            
            # Add header section
            story.append(Paragraph("Audio file", heading_style))
            story.append(Paragraph(mp3_filename, filename_style))
            story.append(Spacer(1, 0.1 * inch))  # Single line
            story.append(Paragraph("Transcript", heading_style))
            story.append(Spacer(1, 0.1 * inch))  # Single line
            
            # Add each segment
            for segment in segments:
                start_time = segment.get('start', 0)
                speaker = segment.get('speaker', 'UNKNOWN')
                text = segment.get('text', '').strip()
                
                # Format timestamp as [HH:MM:SS]
                hours = int(start_time // 3600)
                minutes = int((start_time % 3600) // 60)
                seconds = int(start_time % 60)
                timestamp_str = f"[{hours:02d}:{minutes:02d}:{seconds:02d}] {speaker}"
                
                # Add timestamp and speaker
                story.append(Paragraph(timestamp_str, timestamp_style))
                
                # Add text
                story.append(Paragraph(text, text_style))
                
                # Double space between sections
                story.append(Spacer(1, 0.1 * inch))
            
            # Build PDF
            doc.build(story)
            return True, "PDF generated successfully"
            
        except Exception as e:
            return False, f"PDF generation failed: {str(e)}"

    def on_function_4_generate_outputs(e):
        """Generate TXT, VTT, and PDF outputs from edited JSON transcript."""
        nonlocal selected_file, output_directory, current_epoch
        
        if not selected_file:
            update_status("No file selected. Please select a file first.", is_error=True)
            add_log_message("No file selected")
            return

        if not output_directory or not output_directory.exists():
            update_status("Output directory not found. Please reselect the file.", is_error=True)
            add_log_message("Output directory missing. Reselect the file to recreate it.")
            return

        if not current_epoch:
            update_status("Epoch timestamp not found. Please reselect the file.", is_error=True)
            add_log_message("Epoch timestamp missing. Reselect the file to regenerate it.")
            return

        # Define file paths
        base_name = f"dg_{current_epoch}"
        json_path = output_directory / f"{base_name}_transcript.json"
        txt_path = output_directory / f"{base_name}.txt"
        vtt_path = output_directory / f"{base_name}.vtt"
        pdf_path = output_directory / f"{base_name}.pdf"
        
        # Check if JSON exists
        if not json_path.exists():
            update_status(
                f"⚠️  Transcript JSON not found. Run Function 2 first.",
                is_error=True,
            )
            add_log_message(f"Error: {json_path.name} not found in {output_directory.name}")
            return

        storage.record_function_usage("function_4_generate_outputs")
        update_status("Generating TXT, VTT, and PDF outputs from JSON...")
        add_log_message(f"Reading transcript JSON: {json_path.name}")
        page.update()

        try:
            # Load JSON data
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            segments = data.get("segments", [])
            language = data.get("language", "unknown")
            
            if not segments:
                update_status("⚠️  No segments found in JSON. Cannot generate outputs.", is_error=True)
                add_log_message("Error: JSON contains no segments")
                return
            
            # Generate TXT output with speaker labels
            add_log_message("Generating TXT output...")
            
            # Derive MP3 filename from JSON path
            mp3_filename = json_path.name.replace('_transcript.json', '.mp3')
            
            with open(txt_path, "w", encoding="utf-8") as f:
                # Add header section
                f.write("Audio file\n")
                f.write(f"{mp3_filename}\n\n")
                f.write("Transcript\n\n")
                
                # Add transcript segments with timestamps
                for segment in segments:
                    start_time = segment.get("start", 0)
                    speaker = segment.get("speaker", "UNKNOWN")
                    text = segment.get("text", "").strip()
                    
                    # Format timestamp as [HH:MM:SS]
                    hours = int(start_time // 3600)
                    minutes = int((start_time % 3600) // 60)
                    seconds = int(start_time % 60)
                    
                    f.write(f"[{hours:02d}:{minutes:02d}:{seconds:02d}] {speaker}\n")
                    f.write(f"{text}\n\n")
            
            add_log_message(f"✅ Created: {txt_path.name}")
            
            # Generate VTT output with speaker labels
            add_log_message("Generating VTT output...")
            with open(vtt_path, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                for segment in segments:
                    start_time = format_vtt_timestamp(segment.get("start", 0))
                    end_time = format_vtt_timestamp(segment.get("end", 0))
                    speaker = segment.get("speaker", "UNKNOWN")
                    text = segment.get("text", "").strip()
                    
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"<v {speaker}>{text}</v>\n\n")
            
            add_log_message(f"✅ Created: {vtt_path.name}")
            
            # Generate PDF output
            add_log_message("Generating PDF output...")
            pdf_success, pdf_message = generate_pdf_from_json(json_path, pdf_path, segments)
            if pdf_success:
                add_log_message(f"✅ Created: {pdf_path.name}")
            else:
                add_log_message(f"⚠️  PDF generation warning: {pdf_message}")
            
            add_log_message(f"✅ Output generation complete! Language: {language}")
            add_log_message(f"✅ Output location: {output_directory}")
            
            success_msg = f"✅ Generated TXT, VTT, and PDF outputs from edited JSON!"
            update_status(success_msg)
            
        except json.JSONDecodeError as ex:
            error_msg = f"❌ Invalid JSON format: {str(ex)}"
            add_log_message(error_msg)
            update_status(error_msg, is_error=True)
            logger.error(f"JSON decode error: {str(ex)}")
        except Exception as ex:
            error_msg = f"❌ Output generation failed: {str(ex)}"
            add_log_message(error_msg)
            update_status(error_msg, is_error=True)
            logger.error(f"Output generation error: {str(ex)}")
        
        page.update()

    def format_vtt_timestamp(seconds):
        """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def on_function_5_report_progress(e):
        """Generate a workflow progress report comparing input directory with processed files."""
        nonlocal current_directory
        
        if not current_directory or not current_directory.exists():
            update_status("⚠️  No input directory selected. Please select a directory first.", is_error=True)
            add_log_message("No input directory selected")
            return
        
        storage.record_function_usage("function_5_report_progress")
        update_status("Generating workflow progress report...")
        add_log_message("Scanning input directory and OHW-data...")
        page.update()
        
        try:
            # Scan input directory for audio files
            input_files = {}
            for ext in ['*.wav', '*.mp3']:
                for file_path in current_directory.rglob(ext):
                    stem = file_path.stem
                    if stem not in input_files:
                        input_files[stem] = {'input_path': file_path, 'format': file_path.suffix.lower()}
            
            # Scan OHW-data for processed files
            processed_files = {}
            if DATA_DIR.exists():
                for dir_path in DATA_DIR.iterdir():
                    if dir_path.is_dir() and ' - dg_' in dir_path.name:
                        # Extract basename and epoch from directory name
                        parts = dir_path.name.split(' - dg_')
                        if len(parts) == 2:
                            original_basename = parts[0]  # e.g., "Darrell Hall"
                            epoch = parts[1]
                            dg_name = f"dg_{epoch}"
                            
                            processed_files[original_basename] = {
                                'directory': dir_path,
                                'dg_name': dg_name,
                                'wav': (dir_path / f"{dg_name}.wav").exists(),
                                'mp3': (dir_path / f"{dg_name}.mp3").exists(),
                                'json': (dir_path / f"{dg_name}_transcript.json").exists(),
                                'txt': (dir_path / f"{dg_name}.txt").exists(),
                                'vtt': (dir_path / f"{dg_name}.vtt").exists(),
                                'pdf': (dir_path / f"{dg_name}.pdf").exists(),
                            }
            
            # Calculate statistics
            total_input = len(input_files)
            total_processed = len(processed_files)
            
            complete_count = sum(1 for f in processed_files.values() 
                               if f['mp3'] and f['json'] and f['txt'] and f['vtt'] and f['pdf'])
            in_progress_count = sum(1 for f in processed_files.values()
                                  if not (f['mp3'] and f['json'] and f['txt'] and f['vtt'] and f['pdf'])
                                  and (f['mp3'] or f['json'] or f['txt']))
            
            mp3_count = sum(1 for f in processed_files.values() if f['mp3'])
            json_count = sum(1 for f in processed_files.values() if f['json'])
            txt_count = sum(1 for f in processed_files.values() if f['txt'])
            vtt_count = sum(1 for f in processed_files.values() if f['vtt'])
            pdf_count = sum(1 for f in processed_files.values() if f['pdf'])
            
            # Generate report content
            timestamp = datetime.now()
            report_content = f"""# OHW Workflow Progress Report

**Generated:** {timestamp.strftime('%B %d, %Y at %I:%M %p')}  
**Auto-generated by OHW App - Function 5**

## Overview

This report tracks the processing status of audio files from the input directory through the OHW workflow.

**Input Directory:** `{current_directory}`  
**Output Directory:** `{DATA_DIR}`

## Workflow Stages

1. **Audio (WAV/MP3)** - Original or converted audio
2. **Transcription (JSON)** - Transcript from Function 2 (Whisper or MS Word)
3. **Outputs (TXT, VTT, PDF)** - Final deliverables from Function 4

## Progress Legend

- ✅ **Complete** - All stages finished (MP3, JSON, TXT, VTT, PDF)
- 🟡 **In Progress** - Some stages completed
- ⏳ **Not Started** - Only source file exists in input directory

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Files in Input Directory | {total_input} |
| Processed Directories | {total_processed} |
| ✅ Complete (All stages) | {complete_count} |
| 🟡 In Progress (Some stages) | {in_progress_count} |
| ⏳ Not Started | {total_input - total_processed} |

### Processing Stages Completed

| Stage | Count | Percentage |
|-------|-------|------------|
| MP3 Files | {mp3_count}/{total_processed if total_processed > 0 else 1} | {mp3_count/total_processed*100 if total_processed > 0 else 0:.0f}% |
| JSON Transcripts | {json_count}/{total_processed if total_processed > 0 else 1} | {json_count/total_processed*100 if total_processed > 0 else 0:.0f}% |
| TXT Outputs | {txt_count}/{total_processed if total_processed > 0 else 1} | {txt_count/total_processed*100 if total_processed > 0 else 0:.0f}% |
| VTT Outputs | {vtt_count}/{total_processed if total_processed > 0 else 1} | {vtt_count/total_processed*100 if total_processed > 0 else 0:.0f}% |
| PDF Outputs | {pdf_count}/{total_processed if total_processed > 0 else 1} | {pdf_count/total_processed*100 if total_processed > 0 else 0:.0f}% |

---

## Processed Files Status

"""
            
            # Add complete files
            complete_files = [(name, info) for name, info in sorted(processed_files.items())
                            if info['mp3'] and info['json'] and info['txt'] and info['vtt'] and info['pdf']]
            
            if complete_files:
                report_content += f"### ✅ Complete ({len(complete_files)} files)\n\n"
                for name, info in complete_files:
                    report_content += f"**{name}** (`{info['dg_name']}`)  \n"
                    report_content += f"- ✅ MP3, JSON, TXT, VTT, PDF\n"
                    report_content += f"- Location: `{info['directory'].name}`\n\n"
            
            # Add in-progress files
            in_progress_files = [(name, info) for name, info in sorted(processed_files.items())
                               if not (info['mp3'] and info['json'] and info['txt'] and info['vtt'] and info['pdf'])
                               and (info['mp3'] or info['json'] or info['txt'])]
            
            if in_progress_files:
                report_content += f"### 🟡 In Progress ({len(in_progress_files)} files)\n\n"
                for name, info in in_progress_files:
                    missing = []
                    if not info['mp3']: missing.append('MP3')
                    if not info['json']: missing.append('JSON')
                    if not info['txt']: missing.append('TXT')
                    if not info['vtt']: missing.append('VTT')
                    if not info['pdf']: missing.append('PDF')
                    
                    report_content += f"**{name}** (`{info['dg_name']}`)  \n"
                    report_content += f"- Missing: {', '.join(missing)}\n"
                    report_content += f"- Location: `{info['directory'].name}`\n\n"
            
            # Add unprocessed files
            unprocessed = [name for name in sorted(input_files.keys())
                         if not any(name in processed for processed in processed_files.keys())]
            
            if unprocessed:
                report_content += f"### ⏳ Not Started ({len(unprocessed)} files)\n\n"
                for name in unprocessed:
                    file_info = input_files[name]
                    report_content += f"**{name}{file_info['format']}**  \n"
                    report_content += f"- Status: Source file only\n"
                    report_content += f"- Next: Run Function 1 (if WAV) or Function 2 (if MP3)\n\n"
            
            report_content += f"""---

## Workflow Reminder

For each audio file:

1. **(If WAV) Function 1: Convert WAV to MP3**
2. **Function 2: Transcribe** (choose OpenAI Whisper or MS Word Online mode)
3. **Edit JSON** (fix speaker names, correct text)
4. **Function 4: Generate TXT, VTT & PDF** from edited JSON

---

**Next Report:** Run Function 5 again to update this status report
"""
            
            # Save report with timestamp
            report_filename = f"workflow_progress_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
            report_path = DATA_DIR / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            success_msg = f"✅ Progress report generated: {report_filename}"
            add_log_message(success_msg)
            add_log_message(f"  Saved to: {DATA_DIR}")
            add_log_message(f"  Found {total_input} input files, {total_processed} processed")
            update_status(success_msg)
            
        except Exception as ex:
            error_msg = f"❌ Report generation failed: {str(ex)}"
            add_log_message(error_msg)
            update_status(error_msg, is_error=True)
            logger.error(f"Report generation error: {str(ex)}")
        
        page.update()

    def on_placeholder_function(e):
        """Placeholder for future functions"""
        add_log_message("This function is not yet implemented")
        update_status("Placeholder function — not yet implemented", is_error=False)

    def on_copy_status_click(e):
        """Copy current status text to clipboard."""
        page.set_clipboard(status_text.value or "")
        add_log_message("Status copied to clipboard.")

    def on_clear_log_click(e):
        """Clear the log output field."""
        log_output.value = ""
        page.update()

    # -------------------------------------------------------- function metadata

    # Transcription mode state (Whisper or MS Word)
    transcription_mode = "OpenAI Whisper"  # Default mode

    def set_transcription_mode(mode):
        """Update the transcription mode selection."""
        nonlocal transcription_mode
        transcription_mode = mode
        add_log_message(f"🔄 Transcription mode set to: {mode}")
        update_status(f"Transcription mode: {mode}")

    def on_function_2_transcribe(e):
        """Unified transcription function that delegates to Whisper or MS Word based on mode."""
        if transcription_mode == "OpenAI Whisper":
            on_function_2a_transcribe_whisper(e)
        else:  # MS Word Online
            on_function_2b_ms_word_online(e)

    # Active functions - frequently used
    active_functions = [
        "function_1_wav_to_mp3",
        "function_2_transcribe",
        "function_3_placeholder",
        "function_4_generate_outputs",
        "function_5_report_progress",
    ]

    functions = {
        "function_1_wav_to_mp3": {
            "label": "1: Convert WAV to MP3",
            "icon": "🎵",
            "handler": on_function_1_wav_to_mp3,
            "help_file": "FUNCTION_1_WAV_TO_MP3.md"
        },
        "function_2_transcribe": {
            "label": "2: Transcribe with Selected Mode",
            "icon": "📝",
            "handler": on_function_2_transcribe,
            "help_file": None  # Mode-dependent, shown in handler
        },
        "function_3_placeholder": {
            "label": "3: [Future Function]",
            "icon": "⏳",
            "handler": on_placeholder_function,
            "help_file": None
        },
        "function_4_generate_outputs": {
            "label": "4: Generate TXT, VTT & PDF from JSON",
            "icon": "📄",
            "handler": on_function_4_generate_outputs,
            "help_file": "FUNCTION_4_GENERATE_OUTPUTS.md"
        },
        "function_5_report_progress": {
            "label": "5: Report Workflow Progress",
            "icon": "📊",
            "handler": on_function_5_report_progress,
            "help_file": "FUNCTION_5_REPORT_PROGRESS.md"
        },
    }

    # Help Mode checkbox state
    help_mode_enabled = ft.Ref[ft.Checkbox]()

    def show_help_dialog(function_key):
        """Display the help markdown file for a function"""
        if function_key not in functions:
            return

        func_info = functions[function_key]
        help_file = func_info.get("help_file")
        display_label = func_info['label']  # Default to function label
        
        # Special handling for unified transcription function - use mode-specific help
        if function_key == "function_2_transcribe":
            if transcription_mode == "OpenAI Whisper":
                help_file = "FUNCTION_2A_TRANSCRIBE_WHISPER.md"
                display_label = "2: Transcribe with OpenAI Whisper"
            else:  # MS Word Online
                help_file = "FUNCTION_2B_MS_WORD_ONLINE.md"
                display_label = "2: Transcribe with MS Word Online"

        if not help_file:
            add_log_message(f"No help file available for {display_label}")
            return

        try:
            # Read the markdown file
            with open(help_file, "r", encoding="utf-8") as f:
                markdown_content = f.read()

            add_log_message(f"Displaying help for: {display_label}")

            def close_help_dialog(e):
                help_dialog.open = False
                page.update()

            def copy_help(e):
                page.set_clipboard(markdown_content)
                copy_help_button.text = "Copied!"
                page.update()
                # Reset button text after 2 seconds
                import threading

                def reset_text():
                    import time
                    time.sleep(2)
                    copy_help_button.text = "Copy to Clipboard"
                    page.update()

                threading.Thread(target=reset_text, daemon=True).start()

            copy_help_button = ft.TextButton("Copy to Clipboard", on_click=copy_help)

            help_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Function {display_label}", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"File: {help_file}",
                                size=11,
                                color=ft.Colors.GREY_600,
                                italic=True,
                            ),
                            ft.Container(height=10),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Markdown(
                                            value=markdown_content,
                                            selectable=True,
                                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                            on_tap_link=lambda e: page.launch_url(e.data),
                                        ),
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                ),
                                width=800,
                                height=600,
                                padding=10,
                            ),
                        ],
                        tight=True,
                    ),
                    padding=10,
                ),
                actions=[
                    copy_help_button,
                    ft.TextButton("Close", on_click=close_help_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.overlay.append(help_dialog)
            help_dialog.open = True
            page.update()

        except FileNotFoundError:
            add_log_message(f"Help file not found: {help_file}")
            update_status(f"Help file not found: {help_file}", True)
        except Exception as e:
            add_log_message(f"Error reading help file: {str(e)}")
            update_status(f"Error reading help file: {str(e)}", True)

    def save_speaker_names():
        """Save the current speaker names to persistent storage."""
        names = [
            speaker_name_1.value or "",
            speaker_name_2.value or "",
            speaker_name_3.value or "",
            speaker_name_4.value or "",
            speaker_name_5.value or "",
        ]
        storage.set_speaker_names(names)
        logger.debug(f"Saved speaker names: {names}")

    def get_speaker_names():
        """Get the current speaker names from the UI fields."""
        return [
            speaker_name_1.value or "",
            speaker_name_2.value or "",
            speaker_name_3.value or "",
            speaker_name_4.value or "",
            speaker_name_5.value or "",
        ]

    def execute_selected_function(function_key):
        """Execute the selected function from dropdown or show help if help mode is enabled"""
        if function_key and function_key in functions:
            # Check if help mode is enabled
            if help_mode_enabled.current and help_mode_enabled.current.value:
                # Show help dialog instead of executing
                show_help_dialog(function_key)
                # Clear selection
                active_function_dropdown.value = None
                page.update()
            else:
                # Execute the function normally
                # Call the function handler with a mock event
                class MockEvent:
                    pass

                functions[function_key]["handler"](MockEvent())

                # Refresh dropdown orders after execution
                active_function_dropdown.options = get_sorted_function_options(
                    active_functions
                )
                active_function_dropdown.value = None  # Clear selection
                page.update()

    def get_sorted_function_options(function_list):
        """Get function dropdown options sorted by last use date"""
        from datetime import datetime

        usage_data = storage.get_all_function_usage()

        # Create list of (function_key, last_used_timestamp)
        function_usage = []
        for func_key in function_list:
            usage = usage_data.get(func_key, {})
            last_used = usage.get("last_used")
            # Parse ISO timestamp or use epoch start for never-used functions
            if last_used:
                try:
                    timestamp = datetime.fromisoformat(last_used)
                except:
                    timestamp = datetime.min
            else:
                timestamp = datetime.min

            function_usage.append((func_key, timestamp))

        # Sort by timestamp (most recent first)
        function_usage.sort(key=lambda x: x[1], reverse=True)

        # Create dropdown options
        options = []
        for func_key, timestamp in function_usage:
            func_info = functions[func_key]
            label = f"{func_info['icon']} {func_info['label']}"
            options.append(ft.dropdown.Option(key=func_key, text=label))

        return options

    # ------------------------------------------------------------------ layout

    page.add(
        ft.Column(
            controls=[
                # ---- Title
                ft.Text(
                    "🎙️ OHW — Oral History Workflow",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "A tool for managing creation and ingest of Oral Histories for Digital.Grinnell",
                    size=13,
                    color=ft.Colors.GREY_700,
                    italic=True,
                ),
                ft.Divider(height=5),

                # ---- Inputs section
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Inputs", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "Input Directory",
                                size=14,
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.Row(
                                [
                                    input_directory_field,
                                    ft.ElevatedButton(
                                        "Browse...",
                                        icon=ft.Icons.FOLDER_OPEN,
                                        on_click=on_pick_directory_click,
                                    ),
                                ],
                                spacing=10,
                            ),
                            ft.ElevatedButton(
                                "List WAV and MP3 Files",
                                icon=ft.Icons.REFRESH,
                                on_click=on_list_files_click,
                                tooltip="Scan directory and all subdirectories for audio files",
                            ),
                            file_selection_dropdown,
                        ],
                        spacing=8,
                    ),
                    padding=5,
                ),

                ft.Divider(height=5),

                # ---- Functions section
                ft.Container(
                    content=ft.Column(
                        [
                            # Transcription Mode - Radio buttons
                            ft.Column(
                                [
                                    ft.Text(
                                        "Transcription Mode",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    transcription_mode_radio := ft.RadioGroup(
                                        content=ft.Row(
                                            [
                                                ft.Radio(value="OpenAI Whisper", label="OpenAI Whisper"),
                                                ft.Radio(value="MS Word Online", label="MS Word Online"),
                                            ],
                                            spacing=20,
                                        ),
                                        value="OpenAI Whisper",
                                        on_change=lambda e: set_transcription_mode(e.control.value),
                                    ),
                                ],
                                spacing=5,
                            ),
                            
                            ft.Container(height=10),  # Spacer
                            
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Active Functions",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Text(
                                                "Select and execute workflow functions",
                                                size=12,
                                                italic=True,
                                                color=ft.Colors.GREY_700,
                                            ),
                                            ft.Container(height=5),  # Match Speaker Names spacing
                                            active_function_dropdown := ft.Dropdown(
                                                label="Select Function to Execute",
                                                hint_text="Functions ordered by most recently used",
                                                width=500,
                                                options=[],
                                                on_change=lambda e: execute_selected_function(
                                                    e.control.value
                                                ),
                                            ),
                                            ft.Container(height=5),
                                            ft.Checkbox(
                                                label="Help Mode",
                                                ref=help_mode_enabled,
                                                tooltip="Enable to view help documentation for functions instead of executing them",
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                    ft.Container(width=20),  # Spacer
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Speaker Names",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Text(
                                                "Enter speaker names for transcription (optional, copy/paste enabled)",
                                                size=12,
                                                italic=True,
                                                color=ft.Colors.GREY_700,
                                            ),
                                            ft.Container(height=5),  # Extra space after description
                                            ft.Row(
                                                [
                                                    ft.Column(
                                                        [
                                                            speaker_name_1 := ft.TextField(
                                                                label="Speaker 1",
                                                                hint_text="e.g., John Doe",
                                                                width=200,
                                                                text_size=13,
                                                                on_change=lambda e: save_speaker_names(),
                                                            ),
                                                            ft.Container(height=8),  # Vertical spacing
                                                            speaker_name_2 := ft.TextField(
                                                                label="Speaker 2",
                                                                hint_text="e.g., Jane Smith",
                                                                width=200,
                                                                text_size=13,
                                                                on_change=lambda e: save_speaker_names(),
                                                            ),
                                                            ft.Container(height=8),  # Vertical spacing
                                                            speaker_name_3 := ft.TextField(
                                                                label="Speaker 3",
                                                                hint_text="Optional",
                                                                width=200,
                                                                text_size=13,
                                                                on_change=lambda e: save_speaker_names(),
                                                            ),
                                                        ],
                                                        spacing=0,
                                                    ),
                                                    ft.Container(width=15),  # Horizontal spacing between columns
                                                    ft.Column(
                                                        [
                                                            speaker_name_4 := ft.TextField(
                                                                label="Speaker 4",
                                                                hint_text="Optional",
                                                                width=200,
                                                                text_size=13,
                                                                on_change=lambda e: save_speaker_names(),
                                                            ),
                                                            ft.Container(height=8),  # Vertical spacing
                                                            speaker_name_5 := ft.TextField(
                                                                label="Speaker 5",
                                                                hint_text="Optional",
                                                                width=200,
                                                                text_size=13,
                                                                on_change=lambda e: save_speaker_names(),
                                                            ),
                                                        ],
                                                        spacing=0,
                                                    ),
                                                ],
                                                spacing=0,
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),

                ft.Divider(height=5),

                # ---- Status
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Status",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.COPY,
                                        tooltip="Copy status to clipboard",
                                        on_click=on_copy_status_click,
                                        icon_size=20,
                                    ),
                                ],
                            ),
                            status_text,
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),

                ft.Divider(height=5),

                # ---- Log output
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Log Output",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_SWEEP,
                                        tooltip="Clear log",
                                        on_click=on_clear_log_click,
                                        icon_size=20,
                                    ),
                                ],
                            ),
                            ft.Container(
                                content=log_output,
                                border=ft.border.all(1, ft.Colors.GREY_400),
                                border_radius=5,
                                bgcolor=ft.Colors.GREY_100,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),
            ],
            spacing=4,
        )
    )

    # Populate function dropdowns with sorted options
    active_function_dropdown.options = get_sorted_function_options(active_functions)
    
    # Load saved speaker names
    saved_names = storage.get_speaker_names()
    speaker_name_1.value = saved_names[0] if len(saved_names) > 0 else ""
    speaker_name_2.value = saved_names[1] if len(saved_names) > 1 else ""
    speaker_name_3.value = saved_names[2] if len(saved_names) > 2 else ""
    speaker_name_4.value = saved_names[3] if len(saved_names) > 3 else ""
    speaker_name_5.value = saved_names[4] if len(saved_names) > 4 else ""
    
    page.update()

    logger.info("UI initialised successfully")
    add_log_message("OHW application ready. Select a function to begin.")


if __name__ == "__main__":
    logger.info("Application starting…")
    ft.app(
        target=main,
        assets_dir="assets",
    )
