# Function 4: Generate TXT, VTT & PDF from JSON

## Purpose
Generate final output files (TXT, VTT, and PDF) from the edited JSON transcript created by Function 2a or Function 2b. This allows you to perfect the transcript—fixing speaker names, correcting transcription errors, and adjusting content—before creating the final deliverable files.

## Requirements
- **Prerequisite**: Function 2a or Function 2b must have been run to create the initial JSON transcript
- **JSON file**: `dg_<epoch>_transcript.json` must exist in the output directory
- **Edited content**: You should have edited the JSON to fix speaker names, spelling, etc.

## Usage

1. **First, run Function 2a or Function 2b** to create the initial JSON transcript
2. **Edit the JSON file** located in `~/OHW-data/<basename> - dg_<epoch>/dg_<epoch>_transcript.json`:
   - Change speaker labels (e.g., `"speaker": "SPEAKER_00"` → `"speaker": "John Doe"`)
   - Fix transcription errors in the `"text"` fields
   - Correct spelling and punctuation
   - Adjust timestamps if necessary
3. **Save the edited JSON** (maintain proper JSON format)
4. In the **Active Functions** dropdown, select **"📄 4: Generate TXT, VTT & PDF from JSON"**
5. The function will:
   - Read your edited JSON file
   - Generate a formatted TXT file with speaker labels
   - Generate a VTT subtitle file with speaker tags
   - Generate a formatted PDF with timestamps and speaker labels
6. Monitor the status and log output for progress

## Output Directory

Files are generated in the same output directory as other processing:

```
~/OHW-data/<basename> - dg_<epoch>/
```

For example:
```
~/OHW-data/interview_john_doe - dg_1712345678/
  ├── dg_1712345678.wav                  (from Function 1)
  ├── dg_1712345678.mp3                  (from Function 1)
  ├── dg_1712345678_transcript.json      (from Function 2a/2b, YOU EDIT THIS)
  ├── dg_1712345678.txt                  (from Function 4)
  ├── dg_1712345678.vtt                  (from Function 4)
  └── dg_1712345678.pdf                  (from Function 4)
```

## Output Files

Function 4 generates **3 final output files** from your edited JSON:

### 1. Plain Text (.txt)
- **Filename**: `dg_<epoch>.txt`
- **Contents**: Formatted transcript with timestamps and speaker labels
- **Format**:
  ```
  Audio file
  dg_1775499960.mp3

  Transcript

  [00:00:00] John Doe
  Hello, welcome to the interview.

  [00:00:05] Jane Smith
  Thank you for having me.
  ```
- **Use case**: Easy reading, printing, sharing, archival

### 2. WebVTT (.vtt)
- **Filename**: `dg_<epoch>.vtt`
- **Contents**: Web Video Text Tracks format with timestamps and speaker tags
- **Format**:
  ```
  WEBVTT

  00:00:00.000 --> 00:00:05.420
  <v John Doe>Hello, welcome to the interview.</v>

  00:00:05.420 --> 00:00:08.920
  <v Jane Smith>Thank you for having me.</v>
  ```
- **Use case**: HTML5 video subtitles, web accessibility, video editing

### 3. PDF (.pdf)
- **Filename**: `dg_<epoch>.pdf`
- **Contents**: Formatted transcript with timestamps and speaker labels
- **Format**:
  ```
  Audio file
  dg_1775499960.mp3

  Transcript

  [00:00:00] John Doe
  Hello, welcome to the interview.

  [00:00:05] Jane Smith
  Thank you for having me.
  ```
- **Features**:
  - Audio file header with MP3 filename
  - Transcript header section
  - Timestamps in [HH:MM:SS] format
  - Speaker names on the same line as timestamp
  - Single line break before text
  - Double spacing between transcript sections
- **Use case**: Professional documents, archival, distribution, printing

## JSON Structure

Here's what the JSON structure looks like (simplified):

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 5.42,
      "text": " Hello, welcome to the interview.",
      "speaker": "SPEAKER_00"
    },
    {
      "start": 5.42,
      "end": 8.92,
      "text": " Thank you for having me.",
      "speaker": "SPEAKER_01"
    }
  ]
}
```

**Fields you can edit:**
- `speaker`: Change from SPEAKER_XX to real names
- `text`: Fix transcription errors, spelling, punctuation
- `start`/`end`: Adjust timestamps (in seconds)

**Important:** Keep the JSON structure intact (brackets, commas, quotes)

## Technical Details

### Processing Workflow
1. Reads the JSON file from the output directory
2. Validates JSON structure
3. Generates TXT file with speaker labels and line breaks
4. Generates VTT file with timestamps and speaker voice tags
5. Both files reflect your edits from the JSON

### Speaker Label Formatting
- **TXT**: Speaker names appear on their own line followed by colon (`John Doe:`)
- **VTT**: Speaker names use voice tags (`<v John Doe>text</v>`)
- Speaker changes trigger new paragraphs/segments

### File Handling
- Overwrites existing TXT and VTT files (allows regeneration after JSON edits)
- JSON file is read-only (never modified by this function)
- You can run Function 3 multiple times after editing JSON

## Common Issues

### "Transcript JSON not found"
- Run Function 2 first to create the initial JSON
- Make sure you're using the same file selection
- Check that the JSON exists in the output directory

### "No segments found in JSON"
- JSON file may be corrupted or empty
- Re-run Function 2 to regenerate
- Check JSON syntax with a validator

### "Invalid JSON format"
- JSON editing introduced syntax errors
- Common issues: missing commas, unmatched brackets/quotes
- Use a JSON validator or editor with syntax highlighting
- Consider reverting to backup and re-editing

### Speaker names not appearing correctly
- Check that you edited the `"speaker"` field values
- Ensure speaker names are in quotes
- Names are case-sensitive
- Special characters in names should be properly escaped

## Tips for Editing JSON

1. **Use a proper editor**:
   - VS Code (built-in JSON support)
   - Any text editor with JSON syntax highlighting
   - Online JSON editors (with validation)

2. **Make a backup**:
   - Copy JSON file before editing
   - Keep original in case of mistakes

3. **Validate syntax**:
   - Many editors show errors in real-time
   - Use online JSON validators if unsure

4. **Common edits**:
   - Find/Replace all instances of "SPEAKER_00" with your speaker name
   - Use consistent naming for each speaker
   - Fix obvious transcription errors
   - Remove filler words if desired

5. **Test iteratively**:
   - Make small edits
   - Run Function 3 to generate outputs
   - Review results
   - Edit JSON again if needed
   - Re-run Function 3 (it's fast!)

## Workflow Summary

```
Function 2: MP3 → JSON (with speakers)
   ↓
[YOU EDIT JSON]
   ↓
Function 3: JSON → TXT + VTT (final outputs)
```

This workflow gives you complete control over the final transcript while preserving all the benefits of automated transcription and speaker identification.
