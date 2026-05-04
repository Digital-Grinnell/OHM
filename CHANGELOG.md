# OHM Changelog

All notable changes to the OHM (Oral History Manager) project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses date-based versioning (YYYY-MM-DD).

---

## [2026-05-04]

### Removed
- **OpenAI Whisper transcription entirely removed from codebase**: All Whisper-related code, imports, and documentation have been permanently removed from OHM. Whisper was initially evaluated and implemented as an automated local transcription option, but was ultimately removed due to **licensing concerns** with the OpenAI Whisper model and **lack of built-in speaker diarization** capabilities. MS Word Online, while requiring a subscription, provides superior speaker identification which is essential for oral history workflows. ([#app.py](app.py), [#python_requirements.txt](python_requirements.txt))
  - Removed `openai-whisper`, `torch`, and `torchaudio` dependencies from `python_requirements.txt`
  - Removed Whisper import block and `WHISPER_AVAILABLE` flag from `app.py`
  - Removed entire `on_function_2a_transcribe_whisper()` function (~220 lines)
  - Removed Whisper-specific provenance tracking code
  - Removed all commented code referencing Whisper
  - Deleted `FUNCTION_2A_TRANSCRIBE_WHISPER.md` documentation file
  - Updated all documentation to reflect MS Word Online as the sole transcription method
- **Removed `.env` file and `HF_TOKEN`**: The `.env` file containing the Hugging Face API token (`HF_TOKEN`) is no longer needed since Whisper and its speaker diarization dependencies have been removed. The file has been deleted from the repository.

### Changed
- **Function dropdown ordering**: Functions now always appear in numeric workflow order (0→5) instead of being sorted by most-recent use. The hint text changed from "Functions ordered by most recently used" to "Functions in workflow order (0-5)". Function usage tracking remains in place but is no longer used for sorting. ([#app.py](app.py))

### Fixed
- **Added Function 0 documentation to README.md**: Function 0 (Merge Audio Files) was missing from the README Features section, Workflow section, Help Documentation list, and Privacy & Local Processing section. All sections have been updated to include appropriate references to this optional preprocessing function. ([#README.md](README.md))

---

## [2026-04-16]

### Fixed
#### MP3 source file not copied to output directory (Function 2)

When a workflow started from an MP3 file (rather than a WAV), Function 1 (WAV-to-MP3 conversion) was correctly skipped, but the standardized `dg_<epoch>.mp3` file was never created in the output directory. Function 2 then couldn't find it there and silently fell back to transcribing from the original source path instead of the output-directory copy, contrary to the documented behavior.

**Fix (`app.py`):** In `on_function_2_ms_word_online`, when an MP3 is selected and `dg_<epoch>.mp3` does not yet exist in the output directory, `shutil.copy2` now copies it there before proceeding. A warning is logged and the original path is used as a fallback if the copy fails.

### Changed
#### OpenAI Whisper initially removed from UI (later fully removed in 2026-05-04)

OpenAI Whisper (Function 2a) was initially evaluated as an automated local transcription option but was removed from the OHM interface. The code was commented out but preserved for reference. (See 2026-05-04 entry above for final removal.)

**Initial changes (`app.py`):**
- The **Transcription Mode** radio-button selector (Whisper / MS Word Online) was removed from the Functions panel UI; the widget code was preserved in comments.
- `on_function_2_transcribe` was modified to call only `on_function_2_ms_word_online`.
- The Function 2 dropdown label changed from `"2: Transcribe with Selected Mode"` to `"2: Transcribe with MS Word Online"`.

**Note:** This was a transitional state. In 2026-05-04, all Whisper code and references were permanently removed.

---

## [2026-04-07] - Major Feature Update

### Added

#### Function 0: Merge Audio Files
A new function that concatenates two or more WAV or MP3 files from the current input directory into a single output file. Features include:
- Interactive dialog showing all available audio files in the input directory
- Click **Add →** to queue files in desired merge order
- Visual reordering with **↑ ↓** arrows
- Auto-generated output filename based on common prefix
- Support for mixing WAV and MP3 formats (automatic re-encoding)
- Provenance tracking via `.merge_info.json` sidecar file
- Automatic archiving of source files to `Merged/` subdirectory after successful merge
- Merged subdirectories are excluded from file listings and workflow statistics

**Files:** `app.py`, `FUNCTION_0_MERGE_AUDIO.md`

**Use case:** When a recording session was split across multiple files (e.g., recorder stopped and restarted), this function combines them into a single continuous file before transcription.

#### Function 3: Edit Review Notes
An in-app Markdown editor for creating and editing `review_notes.md` files:
- Opens a dedicated editor dialog for the selected audio file
- Creates new files with a starter template (title, filename, date, blank Notes section)
- Saves to the per-file output directory alongside other deliverables
- Also accessible as the **📋 Review Notes** tab inside the Function 2 dialog
- Edits made in either location share the same file

**Files:** `app.py`, `FUNCTION_3_REVIEW_NOTES.md`

**Use case:** Record reviewer observations, corrections, follow-up questions, or any notes associated with the recording and its transcript.

#### Function 5: Report Workflow Progress
Generates comprehensive progress reports comparing input directory contents with processed files:
- Scans input directory for WAV/MP3 files
- Scans OHM-data for processed directories
- Categorizes files as Complete, In Progress, or Not Started
- Shows statistics and percentages for each processing stage
- Generates timestamped Markdown reports in the working/output directory
- Reports include detailed file-by-file status

**Files:** `app.py`, `FUNCTION_5_REPORT_PROGRESS.md`

**Use case:** Track project progress over time and identify what work remains.

#### Permission PDF Selector
A new input control for selecting a permission/consent PDF from the input directory:
- Pick PDF button opens a dialog listing all PDFs in the input directory
- Selected PDF is automatically copied to the output directory as `permission_form.pdf`
- PDF filename is recorded in transcript JSON provenance notes
- Survives alongside all other deliverables

**Files:** `app.py`

**Use case:** Attach signed permission/consent forms to oral history deliverables.

#### Review Notes Tab in Function 2 Dialog
Function 2 (MS Word Online instructions) now includes a **📋 Review Notes** tab:
- Accessible alongside the **📝 MS Word Instructions** tab
- Provides the same Markdown editor as Function 3
- Changes are saved to the same `review_notes.md` file
- Allows taking notes without leaving the transcription workflow

**Files:** `app.py`

**Use case:** Record significant changes made to Word-generated transcripts while following transcription instructions.

#### Naming Convention Changes
Directory and file naming conventions have been updated for clarity and consistency:
- **Directory separator**: Changed from ` - dg_` to `--dg_` (double-dash with no spaces)
- **Merge suffix**: Changed from `_merged` to `_MERGED` (uppercase)
- **Trailing underscores**: Sanitized basenames no longer end with `_` before the `--dg_` separator

**Examples:**
- Old: `Kerry Bart - dg_1775499960/`
- New: `Kerry_Bart--dg_1775499960/`
- Old: `Interview_merged - dg_1775499960/`
- New: `Interview_MERGED--dg_1775499960/`

**Files affected:** `app.py`, `README.md`

#### Migration Script for Naming Conventions
A migration utility to update existing OHM-data directories to the new naming scheme:
- Detects old-style ` - dg_` separators and converts to `--dg_`
- Converts lowercase `_merged` to uppercase `_MERGED`
- Removes trailing underscores before the separator
- Applies `sanitize_filename()` to both directories and files within
- Preview mode (default) shows what would be changed without making changes
- `--apply` flag executes the actual renames

**Usage:**
```bash
# Preview changes (no files renamed):
python3 migrate_ohm_names.py /path/to/OHM-data

# Apply all renames:
python3 migrate_ohm_names.py --apply /path/to/OHM-data
```

**Files:** `migrate_ohm_names.py`, `README.md`

#### Working/Output Directory Selection
Users can now specify a separate working/output directory:
- Defaults to the same directory as Input Directory
- `OHM-data` subfolder is created automatically inside the chosen directory
- Browse button allows override (e.g., to write to an external drive)
- Selection persists across sessions
- Auto-updates when Input Directory changes (unless manually customized)

**Files:** `app.py`, `README.md`

**Use case:** Write processed files to a different location (e.g., external drive, network share) while keeping source files in their original location.

#### Windows Build Support
Added build script for creating Windows distribution packages:
- `build_windows_zip.sh` creates a ZIP archive for Windows users
- Includes all source files, scripts, and documentation
- Excludes development artifacts (`.venv`, `.git`, etc.)
- Windows users use `run.bat` instead of `run.sh`

**Files:** `build_windows_zip.sh`, `run.bat`, `README.md`

### Changed

#### Function 2 Dialog Enhancements
The MS Word Online instructions dialog has been restructured:
- Tabbed interface with **📝 MS Word Instructions** and **📋 Review Notes** tabs
- Instructions now include a note reminding users to save their review notes
- Copyable fields for easy text selection (directory paths, filenames)
- **Convert to JSON** button remains prominently displayed

**Files:** `app.py`

#### Provenance Tracking Enhancements
The `notes` section of transcript JSON now includes richer provenance metadata:
- **Narrative paragraph**: Human-readable summary of transcription process, source files, speakers, technical details, and system information
- **Merge information**: When audio was created by Function 0, includes merge timestamp, source file list, and codec details
- **Audio technical metadata**: Duration, codec, sample rate, bit rate, channels (via ffprobe)
- **Source file tracking**: Records both the originally-selected file and the actual file transcribed (distinguishes WAV→MP3 conversions)
- **WAV presence detection**: Notes if a WAV file exists in output directory
- **Permission form metadata**: Records permission PDF filename if selected
- **System information**: OS user, hostname, machine type, OS version (hostname omitted from narrative for privacy)
- **MS Word metadata**: Word Online user (last modified by) from DOCX core properties
- **Speaker mapping**: Records interviewer, speaker names, and reviewer

**Files:** `app.py`

#### PDF Output Title and Provenance
Generated PDFs now include:
- **Document Title**: "Oral History Transcript: [Speaker Names]" (derived from speaker mapping)
- **Provenance Section**: Displays the human-readable narrative from JSON provenance notes
- Professional formatting with proper heading hierarchy

**Files:** `app.py`

#### README Documentation
Significant documentation improvements:
- Added **Function 0, 3, and 5** to feature list and workflow guide
- Documented new working/output directory selection
- Added migration script usage instructions
- Updated output structure examples with new naming convention
- Added **Naming convention** section explaining the `--dg_` separator and sanitization
- Updated **Migrating existing OHM-data directories** section
- Enhanced **File Formats** section with provenance examples

**Files:** `README.md`

### Fixed
- Function 2 MS Word Online dialog now correctly handles scenarios where output directory doesn't exist
- File selection now properly extracts epoch from existing `--dg_` directories (previously only worked with ` - dg_`)
- Audio file scanning now excludes `Merged/` subdirectories to avoid listing archived source files

---

## Earlier Releases

### Initial Release Features
The foundational OHM application included:

#### Core Functions
- **Function 1: Convert WAV to MP3** - High-quality audio conversion using FFmpeg
- **Function 2: Transcribe with MS Word Online** - Manual transcription workflow with instructions
- **Function 4: Generate TXT, VTT, CSV & PDF from JSON** - Multi-format output generation

#### Core Features
- Desktop application built with Flet UI framework
- Persistent storage for UI state and settings
- Comprehensive logging system
- Audio file browser and selector
- Help mode with function-specific documentation
- macOS DMG distribution with `.app` bundle
- Automatic virtual environment setup
- Input directory scanning with recursive file discovery

#### Documentation
- Function-specific help files (Markdown)
- README with installation and usage instructions
- Workflow guide and troubleshooting section

---

## Version History

- **v1.2.1** - Latest DMG release (includes Functions 0, 3, 5, and all 2026-04-07 features)
- **v1.2** - Previous DMG release
- **v1.0** - Initial public release

---

## Development Notes

### Removed Features
- **OpenAI Whisper transcription** (Function 2a) - Evaluated and implemented but permanently removed in 2026-05-04 due to licensing concerns with the model and lack of built-in speaker diarization. All code and documentation removed from codebase.

### Planned Features
- Batch processing capabilities
- Additional output formats (DOCX, SRT subtitles)
- Cloud storage integration

---

For the complete project history, see the Git commit log.
