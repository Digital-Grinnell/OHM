# Function 2: Transcribe MP3 using OpenAI Whisper

## Purpose
Transcribe MP3 audio files to text using OpenAI Whisper, generating a clean segment-level JSON file that can be edited before creating final outputs.

> **Development note:** OpenAI Whisper was implemented and evaluated as the automated
> transcription option for Function 2. It was ultimately removed from the OHM UI due to
> slow processing speed on CPU-only hardware and inconsistent output quality compared to
> MS Word Online's cloud service. The code (`on_function_2a_transcribe_whisper`) is
> preserved in `app.py` (commented out) for future reference. MS Word Online is the
> sole active transcription method. See `FUNCTION_2_MS_WORD_ONLINE.md`.

## Requirements
- **Python packages** must be installed:
  - `openai-whisper` - OpenAI's Whisper transcription model
  - `torch` and `torchaudio` - PyTorch dependencies
  - Install with: `pip install openai-whisper torch torchaudio`
- **MP3 or WAV file** - Select an MP3 or WAV file. If a WAV is selected the app will automatically locate the converted MP3 in the output directory.
- **Disk space** - Whisper base model requires ~140MB
- **Time** - Transcription takes 2-5 minutes per hour of audio

## Usage

1. Select **OpenAI Whisper** in the **Transcription Mode** radio buttons
2. In the **Inputs** section, click **Browse...** to select a directory containing your audio files
3. Click **List WAV and MP3 Files** to scan the directory and all subdirectories
4. From the **Select Audio File** dropdown, choose the audio file you want to transcribe
   - WAV or MP3 files are both accepted
   - If you select a WAV file, the app will look for the converted MP3 in the output directory and use it automatically
5. In the **Active Functions** dropdown, select **"2: Transcribe with Selected Mode"**
6. The function will:
   - Load the OpenAI Whisper base model (automatic download on first use)
   - Transcribe the audio (auto-detects language, segment-level only)
   - Add default speaker label SPEAKER_00 to all segments
   - Generate a single clean JSON file
7. Monitor the status and log output for progress
7. **Edit the JSON file** to:
   - Change speaker labels from SPEAKER_00 to actual speaker names
   - Add SPEAKER_01, SPEAKER_02, etc. where speakers change
   - Fix transcription errors or spelling
   - Adjust timestamps if needed
   - Correct text content
8. Use **Function 4** to generate final TXT, VTT, CSV, and PDF outputs from your edited JSON

## Output Directory

The transcription outputs are saved to the same output directory as other file processing:

```
~/OHM-data/<sanitized-basename>--dg_<epoch>/
```

For example, selecting `interview_john_doe.mp3` will use or create:
```
~/OHM-data/interview_john_doe--dg_1712345678/
```

## Output Files

OpenAI Whisper generates **1 JSON file** that serves as the master transcript:

### JSON (.json)
- **Filename**: `dg_<epoch>_transcript.json`
- **Contents**: Complete transcription result including:
  - Detected language
  - Segmented text with timestamps
  - **Speaker label** (defaults to SPEAKER_00 for all segments)
- **Editable fields**:
  - `speaker`: Change to real names and add SPEAKER_01, SPEAKER_02, etc. where speakers change
  - `text`: Fix transcription errors, spelling, punctuation
  - `start`/`end`: Adjust timing if needed
- **Use case**: Master transcript that you edit before generating final outputs

**Workflow:**
1. Function 2a creates the JSON with all segments labeled as SPEAKER_00
2. You edit the JSON file to add speaker changes and perfect the transcript
3. Function 4 reads your edited JSON and generates TXT and VTT outputs

## Technical Details

### OpenAI Whisper
- **Model**: OpenAI Whisper base (~140MB)
- **Language**: Auto-detection (supports 99+ languages)
- **Performance**: Processes audio in a few minutes on modern CPUs
- **Speaker Labels**: Manual - all segments default to SPEAKER_00 for editing

### Processing Workflow
1. Loads OpenAI Whisper model (downloads on first use)
2. Transcribes audio - returns segment-level text with timestamps
3. Adds default SPEAKER_00 label to all segments
4. Saves JSON for manual editing
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

### Whisper not installed
**Problem**: The system cannot find the Whisper libraries
**Solution**: Install required packages:
```bash
pip install openai-whisper torch torchaudio
```

### Not an audio file
**Problem**: Selected file is neither WAV nor MP3
**Solution**: Convert or re-encode the file to MP3 format first. WAV files are also accepted directly.

### Transcription JSON already exists
**Problem**: Output JSON already exists in the output directory
**Result**: The function skips transcription to avoid overwriting existing work
**Solution**: If you want to retranscribe, manually delete the existing JSON file in the output directory

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

### JSON editing tips
- Use a proper JSON editor or VS Code
- Maintain JSON structure (commas, brackets, quotes)
- Don't change field names, only values
- Save file with UTF-8 encoding
- To add speaker changes, change `SPEAKER_00` to different speaker names/numbers at appropriate segments

## Expected Results

A successful transcription will:
- Load the Whisper model (with progress updates)
- Transcribe the audio and detect the language
- Create JSON file with SPEAKER_00 labels
- Log file creation and completion status
- Be ready for manual editing

Example output log:
```
✅ Created: dg_1712345678_transcript.json
✅ Transcription complete! Language: en
✅ Segments: 45
ℹ️  Edit the JSON file to change speaker names from SPEAKER_00, fix spelling, etc.
- ℹ️  Then use **Function 4** to generate TXT, VTT, CSV, and PDF outputs.
```

## Notes
- Whisper model is downloaded once and cached locally
- Transcription quality is excellent for clear speech
- Background noise may affect accuracy
- All segments default to SPEAKER_00 - edit JSON to add speaker changes
- Timestamps are approximate (±1 second)
- The base model provides a good balance of speed and accuracy
- JSON is meant to be edited before final TXT/VTT/CSV/PDF generation
- All processing is local - audio never leaves your computer
