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
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Transcription imports (openai-whisper + pyannote)
try:
    import whisper
    from pyannote.audio import Pipeline
    import torch
    WHISPER_AVAILABLE = True
    # Suppress FP16 warning if no GPU
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Transcription libraries not available. Install with: pip install openai-whisper pyannote.audio torch torchaudio")

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

    def on_function_2_transcribe_mp3(e):
        """Execute Function 2: Transcribe MP3 using OpenAI Whisper with speaker diarization"""
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

        storage.record_function_usage("function_2_transcribe_mp3")
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
                    
                def write(self, text):
                    import time
                    # Update UI every 2 seconds to avoid too frequent updates
                    current_time = time.time()
                    if current_time - self.last_update > 2:
                        if text.strip() and '%' in text:
                            update_status(f"Transcribing: {text.strip()}")
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
            
            # Step 2: Speaker diarization with pyannote.audio
            add_log_message("Running speaker diarization...")
            update_status("Identifying speaker changes...")
            page.update()
            
            speaker_segments = []
            hf_token = os.environ.get("HF_TOKEN")
            try:
                # Load diarization pipeline (try new 'token' parameter, fallback to old name)
                try:
                    diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                except TypeError:
                    # Newer version uses 'token' instead of 'use_auth_token'
                    if hf_token:
                        from huggingface_hub import login
                        login(token=hf_token)
                    diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1"
                    )
                
                if device == "cuda":
                    diarization_pipeline.to(torch.device("cuda"))
                
                # Run diarization - returns speaker labels and time boundaries
                diarization = diarization_pipeline(str(audio_to_transcribe))
                
                # Extract speaker segments
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    speaker_segments.append({
                        "start": turn.start,
                        "end": turn.end,
                        "speaker": speaker
                    })
                
                add_log_message(f"Speaker diarization complete. {len(speaker_segments)} speaker turns found.")
                
            except Exception as diarize_ex:
                add_log_message(f"⚠️  Speaker diarization failed: {str(diarize_ex)}")
                add_log_message("⚠️  Continuing without speaker labels. Set HF_TOKEN if needed.")
                logger.warning(f"Diarization error: {str(diarize_ex)}")
                # Create single speaker segment covering entire audio
                speaker_segments = []
            
            # Step 3: Merge transcription segments with speaker labels by time overlap
            add_log_message("Merging transcription with speaker labels...")
            update_status("Merging transcription with speaker labels...")
            page.update()
            
            def get_speaker_for_segment(seg_start, seg_end, speaker_segs):
                """Find the speaker with maximum overlap with this segment."""
                if not speaker_segs:
                    return "SPEAKER_00"
                
                max_overlap = 0
                best_speaker = "SPEAKER_00"
                
                for spk in speaker_segs:
                    # Calculate overlap
                    overlap_start = max(seg_start, spk["start"])
                    overlap_end = min(seg_end, spk["end"])
                    overlap = max(0, overlap_end - overlap_start)
                    
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_speaker = spk["speaker"]
                
                return best_speaker
            
            # Assign speaker to each transcript segment
            final_segments = []
            for seg in transcript_segments:
                speaker = get_speaker_for_segment(seg["start"], seg["end"], speaker_segments)
                final_segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "speaker": speaker
                })
            
            # Step 4: Save JSON
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
            add_log_message(f"✅ Segments: {len(final_segments)} with speaker labels")
            add_log_message(f"✅ Output location: {output_directory}")
            add_log_message("ℹ️  Edit the JSON file to fix speaker names, spelling, etc.")
            add_log_message("ℹ️  Then use Function 3 to generate TXT and VTT outputs.")
            
            success_msg = f"✅ Transcription complete! {len(final_segments)} segments with speaker labels."
            update_status(success_msg)
            
        except Exception as ex:
            error_msg = f"❌ Transcription failed: {str(ex)}"
            add_log_message(error_msg)
            update_status(error_msg, is_error=True)
            logger.error(f"Transcription error: {str(ex)}")
        
        page.update()

    def on_function_3_generate_outputs(e):
        """Generate TXT and VTT outputs from edited JSON transcript."""
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
        
        # Check if JSON exists
        if not json_path.exists():
            update_status(
                f"⚠️  Transcript JSON not found. Run Function 2 first.",
                is_error=True,
            )
            add_log_message(f"Error: {json_path.name} not found in {output_directory.name}")
            return

        storage.record_function_usage("function_3_generate_outputs")
        update_status("Generating TXT and VTT outputs from JSON...")
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
            with open(txt_path, "w", encoding="utf-8") as f:
                current_speaker = None
                for segment in segments:
                    speaker = segment.get("speaker", "UNKNOWN")
                    text = segment.get("text", "").strip()
                    
                    if speaker != current_speaker:
                        # New speaker, add speaker label
                        f.write(f"\n{speaker}:\n")
                        current_speaker = speaker
                    
                    f.write(f"{text}\n")
            
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
            add_log_message(f"✅ Output generation complete! Language: {language}")
            add_log_message(f"✅ Output location: {output_directory}")
            
            success_msg = f"✅ Generated TXT and VTT outputs from edited JSON!"
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

    # Active functions - frequently used
    active_functions = [
        "function_1_wav_to_mp3",
        "function_2_transcribe_mp3",
        "function_3_generate_outputs",
    ]

    # Inactive functions - placeholders for future development
    inactive_functions = [
        "function_placeholder",
    ]

    functions = {
        "function_1_wav_to_mp3": {
            "label": "1: Convert WAV to MP3",
            "icon": "🎵",
            "handler": on_function_1_wav_to_mp3,
            "help_file": "FUNCTION_1_WAV_TO_MP3.md"
        },
        "function_2_transcribe_mp3": {
            "label": "2: Transcribe MP3 using Whisper",
            "icon": "📝",
            "handler": on_function_2_transcribe_mp3,
            "help_file": "FUNCTION_2_TRANSCRIBE_MP3.md"
        },
        "function_3_generate_outputs": {
            "label": "3: Generate TXT & VTT from JSON",
            "icon": "📄",
            "handler": on_function_3_generate_outputs,
            "help_file": "FUNCTION_3_GENERATE_OUTPUTS.md"
        },
        "function_placeholder": {
            "label": "Placeholder: Future Function",
            "icon": "📋",
            "handler": on_placeholder_function,
            "help_file": None
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

        if not help_file:
            add_log_message(f"No help file available for {func_info['label']}")
            return

        try:
            # Read the markdown file
            with open(help_file, "r", encoding="utf-8") as f:
                markdown_content = f.read()

            add_log_message(f"Displaying help for: {func_info['label']}")

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
                title=ft.Text(f"📖 Help: {func_info['label']}", weight=ft.FontWeight.BOLD),
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

    def execute_selected_function(function_key):
        """Execute the selected function from dropdown or show help if help mode is enabled"""
        if function_key and function_key in functions:
            # Check if help mode is enabled
            if help_mode_enabled.current and help_mode_enabled.current.value:
                # Show help dialog instead of executing
                show_help_dialog(function_key)
                # Clear selection
                active_function_dropdown.value = None
                inactive_function_dropdown.value = None
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
                inactive_function_dropdown.options = get_sorted_function_options(
                    inactive_functions
                )
                active_function_dropdown.value = None  # Clear selection
                inactive_function_dropdown.value = None  # Clear selection
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
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Active Functions",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            active_function_dropdown := ft.Dropdown(
                                                label="Select Function to Execute",
                                                hint_text="Functions ordered by most recently used",
                                                width=500,
                                                options=[],
                                                on_change=lambda e: execute_selected_function(
                                                    e.control.value
                                                ),
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                    ft.Container(width=20),  # Spacer
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Inactive Functions",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            inactive_function_dropdown := ft.Dropdown(
                                                label="Select Inactive Function",
                                                hint_text="Less frequently used",
                                                width=300,
                                                options=[],
                                                on_change=lambda e: execute_selected_function(
                                                    e.control.value
                                                ),
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ]
                            ),
                            ft.Checkbox(
                                label="Help Mode",
                                ref=help_mode_enabled,
                                tooltip="Enable to view help documentation for functions instead of executing them",
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
    inactive_function_dropdown.options = get_sorted_function_options(inactive_functions)
    page.update()

    logger.info("UI initialised successfully")
    add_log_message("OHW application ready. Select a function to begin.")


if __name__ == "__main__":
    logger.info("Application starting…")
    ft.app(
        target=main,
        assets_dir="assets",
    )
