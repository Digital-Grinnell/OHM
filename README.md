# OHW - Oral History Workflow

OHW is a desktop application built with Flet that streamlines the creation and processing of oral history recordings for Digital.Grinnell. The application provides an integrated workflow from audio conversion through transcription to final deliverables.

## Features

### Function 1: Convert WAV to MP3
- Converts large WAV audio files to compressed MP3 format
- Uses FFmpeg for high-quality conversion
- Preserves audio quality while reducing file size
- Required for files that need to be uploaded to transcription services

### Function 2: Transcribe with Selected Mode
Choose between two transcription methods:

#### OpenAI Whisper Mode (Automatic)
- **Local processing** - runs entirely on your machine
- **Automated transcription** using OpenAI's Whisper model
- Generates timestamped segments with speaker labels (default: SPEAKER_00)
- Creates JSON output ready for editing
- No cloud services or subscriptions required

#### MS Word Online Mode (Manual)
- **Cloud-based** Microsoft transcription service
- **Requires Microsoft 365 subscription**
- Uses Word's built-in Transcribe feature
- Provides speaker identification
- Includes **automated DOCX to JSON conversion** with button click
- Automatically maps Word speaker labels to your custom speaker names

### Function 3: [Future Function]
Placeholder for additional processing capabilities

### Function 4: Generate TXT, VTT & PDF from JSON
- Reads edited JSON transcript (from Function 2)
- Generates three output formats:
  - **TXT** - Plain text with timestamps and speaker labels
  - **VTT** - WebVTT subtitle format for video players
  - **PDF** - Formatted document with headers and timestamps
- All outputs include:
  - Audio file header
  - Transcript section
  - Timestamps in [HH:MM:SS] format
  - Speaker names
  - Professional formatting

### Function 5: Report Workflow Progress
- Scans input directory and OHW-data for status comparison
- Generates timestamped markdown reports
- Tracks completion across all workflow stages
- Identifies:
  - Complete files (all stages finished)
  - In-progress files (partial completion)
  - Not started files (source only)
- Shows statistics and percentages
- Helps track project progress over time

## Additional Features

### Speaker Names Management
- **5 persistent speaker name fields** in the UI
- Names are saved automatically and persist across sessions
- Used in MS Word Online instructions
- Applied when converting DOCX to JSON
- Maintains exact formatting (no uppercase conversion or underscores)

### Transcription Mode Selection
- **Radio button interface** to select transcription method
- Choice persists during session
- Help documentation adapts to selected mode
- Seamless switching between Whisper and MS Word workflows

### Help Mode
- **Built-in help documentation** for each function
- Click Help Mode checkbox before selecting a function
- Displays detailed instructions in scrollable dialogs
- Context-sensitive help based on transcription mode

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OHW
   ```

2. **Run the application**
   ```bash
   ./run.sh
   ```
   
   This script will:
   - Create a Python virtual environment (`.venv`)
   - Install all dependencies from `python_requirements.txt`
   - Launch the OHW application

## Requirements

### System Requirements
- **macOS** (primary platform)
- **Python 3.8+**
- **FFmpeg** (for WAV to MP3 conversion)
  ```bash
  brew install ffmpeg
  ```

### Python Dependencies
All dependencies are installed automatically by `run.sh`:
- `flet==0.25.2` - Desktop UI framework
- `openai-whisper` - Automatic transcription
- `torch>=2.0.0` - Machine learning backend for Whisper
- `torchaudio>=2.0.0` - Audio processing
- `python-docx` - DOCX file parsing
- `reportlab` - PDF generation

### Optional Requirements
- **Microsoft 365 subscription** (only for MS Word Online transcription mode)

## Workflow

### Complete Oral History Processing Workflow

1. **Select Input Directory**
   - Browse to folder containing WAV or MP3 audio files
   - Click "List WAV and MP3 Files" to scan
   - Select an audio file from the dropdown

2. **Convert Audio** (if needed)
   - If you have WAV files, run **Function 1** to convert to MP3
   - MP3s are required for cloud transcription services
   - Skip this step if you already have MP3 files

3. **Choose Transcription Mode**
   - Select **OpenAI Whisper** for automated local processing
   - Select **MS Word Online** for manual cloud-based transcription

4. **Transcribe Audio**
   - Run **Function 2** to create initial transcript
   - **Whisper**: Automatic processing, creates JSON directly
   - **MS Word Online**: Follow instructions, download DOCX, click "Convert to JSON"

5. **Edit Speaker Names** (Optional but recommended)
   - Enter speaker names in the 5 text fields in the UI
   - Names are used in MS Word instructions and DOCX conversion
   - Names persist across sessions

6. **Edit Transcript JSON**
   - Open the generated `dg_<epoch>_transcript.json` file
   - Fix speaker labels (e.g., change "SPEAKER_00" to actual names)
   - Correct transcription errors
   - Adjust timing if necessary
   - Save the edited JSON

7. **Generate Final Outputs**
   - Run **Function 4** to create deliverables
   - Generates: TXT, VTT, and PDF files
   - All formats include timestamps and speaker labels

8. **Track Progress** (Optional)
   - Run **Function 5** to generate progress report
   - Review what's complete and what needs work
   - Reports saved with timestamps in `~/OHW-data/`

## Output Structure

All processed files are organized in directories under `~/OHW-data/`:

```
~/OHW-data/
├── <basename> - dg_<epoch>/
│   ├── dg_<epoch>.wav          # Original or converted audio
│   ├── dg_<epoch>.mp3          # Compressed audio
│   ├── dg_<epoch>_transcript.json  # Editable transcript
│   ├── dg_<epoch>.txt          # Plain text output
│   ├── dg_<epoch>.vtt          # Video subtitle format
│   └── dg_<epoch>.pdf          # Formatted document
└── workflow_progress_YYYYMMDD_HHMMSS.md  # Progress reports
```

### File Formats

#### JSON Transcript
```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 5.42,
      "text": "Hello, welcome to the interview.",
      "speaker": "John Doe"
    }
  ]
}
```

#### TXT/PDF Format
```
Audio file
dg_1775499960.mp3

Transcript

[00:00:00] John Doe
Hello, welcome to the interview.

[00:00:05] Jane Smith
Thank you for having me.
```

## Help Documentation

Each function has detailed help documentation accessible via Help Mode:

- **FUNCTION_1_WAV_TO_MP3.md** - Audio conversion guide
- **FUNCTION_2A_TRANSCRIBE_WHISPER.md** - Whisper transcription guide
- **FUNCTION_2B_MS_WORD_ONLINE.md** - MS Word Online guide
- **FUNCTION_4_GENERATE_OUTPUTS.md** - Output generation guide
- **FUNCTION_5_REPORT_PROGRESS.md** - Progress reporting guide

## Privacy & Local Processing

- **Functions 1, 2 (Whisper), 4, and 5** run entirely locally
- **No audio or text is uploaded to external servers** (except MS Word Online mode)
- **Function 2 (MS Word Online)** uses Microsoft's cloud service
- All processing preserves original files
- Speaker names and settings stored locally in JSON

## Troubleshooting

### FFmpeg Not Found
```bash
brew install ffmpeg
```

### Whisper Not Working
- Ensure `torch` and `torchaudio` are installed
- Check that you have sufficient disk space for the Whisper model (~140MB)
- First run downloads the model automatically

### MS Word Transcription Issues
- Ensure you have an active Microsoft 365 subscription
- Word Online transcription requires < 200MB audio files
- Use Function 1 to convert/compress large files first

### PDF Generation Fails
- Ensure `reportlab` is installed: `pip install reportlab`
- Check that output directory exists and is writable

## Development

The application uses:
- **Flet** for the desktop UI framework
- **OpenAI Whisper** for automated transcription
- **python-docx** for DOCX file parsing
- **reportlab** for PDF generation
- **Persistent storage** via JSON for settings and usage tracking

### Log Files
Application logs are stored in:
```
~/OHW-data/logfiles/ohw_YYYYMMDD_HHMMSS.log
```

## License

[License information to be added]

## Contributing

[Contribution guidelines to be added]

## Support

For questions or issues, please refer to the function-specific help documentation or contact the Digital.Grinnell team.
