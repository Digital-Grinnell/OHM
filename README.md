# OHW
OHW stands for Oral History Workflow, an app created specifically to help manage creation and ingest of Oral Histories for Digital.Grinnell.

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
   - Create a Python virtual environment
   - Install all dependencies
   - Launch the OHW application

## Features

- **Function 1**: Convert WAV to MP3
- **Function 2**: Transcribe MP3 using OpenAI Whisper
- **Function 3**: Generate TXT and VTT outputs from edited transcript JSON

All processing is done locally on your machine. Your audio files never leave your computer.
