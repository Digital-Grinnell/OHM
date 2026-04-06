# OHW
OHW stands for Oral History Workflow, an app created specifically to help manage creation and ingest of Oral Histories for Digital.Grinnell.

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OHW
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Hugging Face token:
   - Sign up at https://huggingface.co/join (free)
   - Accept model terms at https://huggingface.co/pyannote/speaker-diarization-3.1
   - Get your token at https://huggingface.co/settings/tokens
   - Add to `.env`: `HF_TOKEN=hf_your_token_here`

3. **Run the application**
   ```bash
   ./run.sh
   ```
   
   This script will:
   - Create a Python virtual environment
   - Install all dependencies
   - Launch the OHW application

## Features

- **Function 1**: Convert WAV to MP3
- **Function 2**: Transcribe MP3 using OpenAI Whisper with speaker diarization
- **Function 3**: Generate TXT and VTT outputs from edited transcript JSON

All processing is done locally on your machine. Your audio files never leave your computer.
