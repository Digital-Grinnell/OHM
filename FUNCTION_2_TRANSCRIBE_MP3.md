# Function 2: Transcribe MP3 using OpenAI Whisper

## Purpose
Transcribe MP3 audio files to text using OpenAI Whisper with pyannote.audio for speaker identification, generating a clean segment-level JSON file that can be edited before creating final outputs.

## Requirements
- **Python packages** must be installed:
  - `openai-whisper` - OpenAI's Whisper transcription model
  - `pyannote.audio` - Speaker diarization
  - `torch` and `torchaudio` - PyTorch dependencies
  - `python-dotenv` - Environment variable management
  - Install with: `pip install openai-whisper pyannote.audio torch torchaudio python-dotenv`
- **MP3 file** - Select an MP3 file (either standalone or one created by Function 1)
- **Disk space** - Models require ~500MB total (base model + diarization)
- **Time** - Transcription takes 2-5 minutes per hour of audio
- **Hugging Face Token** - Required for speaker diarization (free account at huggingface.co)
  - Sign up at: https://huggingface.co/join
  - Accept model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1
  - Get token from: https://huggingface.co/settings/tokens
  - **Add to `.env` file**: Create a `.env` file in the project root with:
    ```
    HF_TOKEN=hf_your_token_here
    ```
  - The app will automatically load your token from this file

## Usage

1. In the **Inputs** section, click **Browse...** to select a directory containing your audio files
2. Click **List WAV and MP3 Files** to scan the directory and all subdirectories
3. From the **Select Audio File** dropdown, choose the MP3 file you want to transcribe
   - Files are displayed with relative paths (e.g., `subdir/file.mp3`)
   - The app searches `~/OHW-data/` for an existing directory matching the file's basename
   - If found, it reuses that directory and epoch timestamp
   - If not found, it creates a new directory named `<basename> - dg_<epoch>`
4. In the **Active Functions** dropdown, select **"📝 2: Transcribe MP3 using Whisper"**
5. The function will:
   - Load the OpenAI Whisper base model (automatic download on first use)
   - Transcribe the audio (auto-detects language, segment-level only)
   - Run pyannote.audio speaker diarization (requires HF_TOKEN)
   - Identify speaker changes and label them (SPEAKER_00, SPEAKER_01, etc.)
   - Merge transcription with speaker labels by time overlap
   - Generate a single clean JSON file
6. Monitor the status and log output for progress
7. **Edit the JSON file** to:
   - Change speaker labels (e.g., SPEAKER_00 → "John Doe")
   - Fix transcription errors or spelling
   - Adjust timestamps if needed
   - Correct text content
8. Use **Function 3** to generate final TXT and VTT outputs from your edited JSON

## Output Directory

The transcription outputs are saved to the same output directory as other file processing:

```
~/OHW-data/<basename> - dg_<epoch>/
```

For example, selecting `interview_john_doe.mp3` will use or create:
```
~/OHW-data/interview_john_doe - dg_1712345678/
```

## Output Files

OpenAI Whisper generates **1 JSON file** that serves as the master transcript:

### JSON (.json)
- **Filename**: `dg_<epoch>_transcript.json`
- **Contents**: Complete transcription result including:
  - Detected language
  - Segmented text with timestamps
  - **Speaker labels** (SPEAKER_00, SPEAKER_01, SPEAKER_02, etc.)
  - Word-level timestamps
- **Editable fields**:
  - `speaker`: Change to real names (e.g., "John Doe", "Jane Smith")
  - `text`: Fix transcription errors, spelling, punctuation
  - `start`/`end`: Adjust timing if needed
- **Use case**: Master transcript that you edit before generating final outputs

**Workflow:**
1. Function 2 creates the JSON with speaker labels
2. You edit the JSON file to perfect the transcript
3. Function 3 reads your edited JSON and generates TXT and VTT outputs

## Technical Details

### OpenAI Whisper + Pyannote.audio
- **Model**: OpenAI Whisper base (~140MB)
- **Diarization**: pyannote.audio 3.1 neural diarization (~400MB)
- **Language**: Auto-detection (supports 99+ languages)
- **Performance**: Processes audio in a few minutes on modern CPUs
- **Speaker Diarization**: Identifies speaker change points (no name inference)

### Processing Workflow
1. Loads OpenAI Whisper model (downloads on first use)
2. Transcribes audio - returns segment-level text with timestamps (no word-level data)
3. Loads pyannote.audio diarization pipeline (requires HF_TOKEN)
4. Identifies speaker segments from audio (returns SPEAKER_00, SPEAKER_01, etc.)
5. Merges transcription segments with speaker labels by time overlap
6. Saves clean JSON with: text, start, end, speaker for each segment

### Speaker Labels
- Speakers are automatically labeled as SPEAKER_00, SPEAKER_01, etc.
- You should edit these to real names in the JSON file
- Speaker identification works best with:
  - Clear audio quality
  - Multiple distinct voices
  - Minimal background noise
  - Speakers taking turns (not talking over each other)

### File Handling
- If JSON already exists, the function is skipped
- Uses the `dg_<epoch>.mp3` file from output directory if available
- Falls back to selected source MP3 if not found
- **Important**: Edit the JSON before running Function 3 to generate final outputs

## Common Issues

### "No Hugging Face token found" or Diarization Failed
- Speaker diarization requires HF authentication
- Create free account at huggingface.co
- Get token from Settings → Access Tokens
- Accept terms for pyannote models: https://huggingface.co/pyannote/speaker-diarization-3.1
- Add token to `.env` file in project root:
  ```
  HF_TOKEN=hf_your_token_here
  ```
- Restart the application
- If diarization fails, function continues with single speaker (SPEAKER_00)

### Poor speaker identification
- Check audio quality (reduce background noise)
- Ensure speakers have distinct voices
- Diarization works best with 2-4 speakers
- Consider re-recording if audio is very poor

### Slow processing
- First run downloads models (~500MB)
- GPU acceleration recommended for long audio
- Disable diarization if you don't need speaker labels

### JSON editing tips
- Use a proper JSON editor or VS Code
- Maintain JSON structure (commas, brackets, quotes)
- Don't change field names, only values
- Save file with UTF-8 encoding

## Expected Results

A successful transcription will:
- Load the Whisper model (with progress updates)
- Transcribe the audio and detect the language
- Create 5 output files in the output directory
- Log each file creation
- Display language detected and completion status

Example output log:
```
✅ Created: dg_1712345678.txt
✅ Created: dg_1712345678_transcript.json
✅ Created: dg_1712345678.vtt
✅ Created: dg_1712345678.srt
✅ Created: dg_1712345678.docx
✅ Transcription complete! Language detected: English
```

## Common Issues

### Whisper not installed
**Problem**: The system cannot find the Whisper libraries
**Solution**: Install required packages:
```bash
pip install openai-whisper python-docx torch torchaudio
```

### Not an MP3 file
**Problem**: Selected file is a WAV or other format
**Solution**: Only MP3 files can be transcribed with this function. Convert WAV to MP3 using Function 1 first.

### Transcription files already exist
**Problem**: Output files already exist in the output directory
**Result**: The function skips transcription to avoid overwriting existing work
**Solution**: If you want to retranscribe, manually delete the existing transcription files in the output directory

### Slow transcription
**Problem**: Transcription takes longer than expected
**Notes**: 
- Transcription speed depends on CPU performance
- Typically processes 2-10x faster than real-time
- First run downloads the model (~140MB)
- GPU acceleration is available but not required

### Model download fails
**Problem**: First-time model download times out or fails
**Solution**: 
- Check internet connection
- Retry the operation
- Manually download from: https://github.com/openai/whisper

## Notes
- Whisper model is downloaded once and cached locally
- Transcription quality is excellent for clear speech
- Background noise may affect accuracy
- Multiple speakers are transcribed but not automatically labeled
- Timestamps are approximate (±1 second)
- The base model provides a good balance of speed and accuracy
- All output formats contain the same transcription, just formatted differently
- Transcription outputs are suitable for Digital.Grinnell oral history archival workflows
- The DOCX format is recommended for human editing and annotation
- VTT and SRT formats are ideal if you plan to create video versions
