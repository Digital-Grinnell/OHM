# Function 2: Transcribe with MS Word Online

## Purpose
Provide step-by-step instructions for manual transcription using Microsoft Word Online's built-in Transcribe feature, using Microsoft's cloud-based transcription service.

> **Note:** MS Word Online is the sole active transcription method in OHM. OpenAI Whisper
> (local, CPU-based) was evaluated as an alternative but was removed from the UI due to
> slow performance on non-GPU hardware and output quality concerns. Its code and documentation
> are preserved for reference in `FUNCTION_2A_TRANSCRIBE_WHISPER.md`.

## Requirements
- **Microsoft 365 subscription** - Required for Word Online transcription feature
- **MP3 or WAV file** - Select an MP3 or WAV file. If a WAV is selected, the app will automatically locate the converted MP3 in the output directory.
- **Internet connection** - Transcription happens in the cloud
- **Modern web browser** - Chrome, Firefox, Safari, or Edge

## When to Use This Mode

Use MS Word Online mode instead of Whisper mode when:
- You prefer Microsoft's transcription service over locally-run Whisper
- You don't have local compute resources for Whisper
- You want to use Word's built-in speaker identification
- You're already comfortable with Word Online

**Note:** Whisper mode is recommended for most users as it runs entirely locally and requires no subscription.

## Usage

1. Select **MS Word Online** in the **Transcription Mode** radio buttons
2. In the **Inputs** section, click **Browse...** to select a directory containing your audio files
3. Click **List WAV and MP3 Files** to scan the directory and all subdirectories
4. From the **Select Audio File** dropdown, choose the MP3 file you want to transcribe
5. **(Optional)** Enter names in the **Individuals** panel
   - **Interviewer** — defaults to "Interviewer" if left blank
   - **Speaker 1–4** — the oral history subject(s)
   - **Reviewed By** — reviewer/editor name (omitted from narrative if blank)
   - Names are displayed in the instructions dialog and applied during DOCX-to-JSON conversion
   - Stored with normalised keys: `Interviewer`, `Speaker 1` … `Speaker 4`, `Reviewed By`
6. In the **Active Functions** dropdown, select **"2: Transcribe with Selected Mode"**
7. A dialog will appear with two tabs:
   - **📝 MS Word Instructions** — the step-by-step transcription workflow (default view)
   - **📋 Review Notes** — an inline Markdown editor for recording changes and observations
8. Follow the instructions to complete the transcription process
9. Switch to the **Review Notes** tab at any time to jot down notes; click **Save Notes** to persist them

## Transcription Workflow

The function displays instructions for this multi-step workflow:

### STEP 1: Open Microsoft Word Online
- Navigate to https://www.office.com/launch/word
- Sign in with your Microsoft 365 account
- Create a blank document

### STEP 2: Set Document Name
- Rename the document to match your audio file name
- This ensures consistency across all output files

### STEP 3: Start Transcription
- Access the Transcribe feature (Home tab → Dictate dropdown → Transcribe)
- Upload your MP3 file
- Wait for Microsoft's service to process the audio
- Processing time varies by file length (typically a few minutes)

### STEP 4: Review & Edit
- Review the transcription in the Transcribe pane
- Edit speaker names (replace "Speaker 1" with actual names)
- Fix any transcription errors
- **💡 Use the Review Notes tab in the dialog to record significant changes you make to the Word-generated transcript. Remember to SAVE your notes.**
- **⚠️  CRITICAL: Click 'Add to document' → select 'With Speakers and Timestamps'**
  - This option is required to preserve speaker labels and timestamps in the DOCX file
  - Using plain 'Add to document' (without speakers/timestamps) will produce a file the converter cannot parse correctly

### STEP 5: Save as DOCX
Save the DOCX directly to your output directory — no moving needed.

Before you begin the download, copy these two values from the instructions dialog:
- **Save To (Output Directory):** shown as a copyable field in the dialog — the full path to `~/OHM-data/<sanitized-basename>--dg_<epoch>/`
- **Save As (Filename):** shown as a copyable field in the dialog — e.g. `dg_<epoch>.docx`

Then:
- Click the **File** menu in Word
- Select **Create a Copy**
- Select **Download a copy** and confirm
- When the browser's Save dialog appears, navigate to the **Output Directory** path above, set the filename to the **Save As** value, and click **Save**

> **If your browser saves automatically to Downloads** (no Save dialog): move the file
> from Downloads to the output directory and rename it to match the expected filename
> before clicking **Convert to JSON**.

### STEP 6: Convert to JSON
- Once the DOCX is in the output directory with the correct filename, click the **"Convert to JSON"** button
- The function will automatically:
  - Parse the DOCX transcription file
  - Extract timestamps and speaker labels from Word's format
  - Map Word's speakers to your custom speaker names (in order of appearance)
  - Create a JSON file in Whisper format
- **Speaker Name Mapping:**
  - 1st speaker in Word → 1st name in Speaker Names fields
  - 2nd speaker in Word → 2nd name in Speaker Names fields
  - etc.
  - Names are used exactly as entered (case and spaces preserved)
- File created:
  - `dg_<epoch>_transcript.json` - Whisper-format transcript with your speaker names

**Note:** The conversion expects Word's transcription format with timestamps like `00:00:00 Speaker` and text on following lines.

### STEP 7: Generate Final Outputs
- After conversion completes, use **Function 4** to generate TXT, VTT, and PDF outputs from the JSON

## Output Directory

The instructions remind you to save files in:
```
~/OHM-data/<sanitized-basename>--dg_<epoch>/
```

This is the same directory used by all other functions for consistency.

## Comparison: MS Word Online vs Whisper

| Feature | Whisper Mode | MS Word Online Mode |
|---------|---------------------|----------------------------|
| **Processing** | Local on your computer | Cloud (Microsoft servers) |
| **Cost** | Free | Requires Microsoft 365 subscription |
| **Privacy** | 100% local | Audio uploaded to Microsoft |
| **Internet** | Not required (after model download) | Required |
| **Speed** | 2-5 minutes per hour of audio | Varies, typically similar |
| **Automation** | Fully automated | Requires manual steps |
| **JSON Creation** | Automatic | Automatic (via Convert button) |
| **Speaker Names** | Manual editing after | Applied during conversion |
| **Best For** | Privacy, offline work, automation | Users with M365 subscription |

## Review Notes Integration

The Function 2 dialog includes a built-in **Review Notes** tab so you can record observations without switching away from the transcription instructions.

- The tab opens the same `review_notes.md` file used by Function 3
- If the file already exists its current content is loaded; otherwise a dated starter template is pre-filled
- Click **Save Notes** inside the tab to write the file at any time
- Changes saved here are immediately visible if you later open Function 3, and vice versa
- The file is stored alongside all other per-file outputs:
  ```
  ~/OHM-data/<sanitized-basename>--dg_<epoch>/review_notes.md
  ```

## Important Notes

### Microsoft 365 Subscription Required
- The Transcribe feature is only available with a Microsoft 365 subscription
- Free Word Online accounts cannot access this feature
- Check your subscription status before attempting transcription

### Automated Conversion
- The **"Convert to JSON"** button eliminates manual JSON creation
- Automatically parses Word's transcription format
- Maps speakers to your custom names from the Speaker Names fields
- Preserves exact name formatting (no automatic uppercase or underscores)
- Creates Whisper-compatible JSON instantly

### Manual JSON Creation No Longer Required
- Previous versions required manually extracting and formatting JSON
- The automated conversion button handles this automatically
- Save the DOCX directly to the output directory during download (path and filename shown in the dialog), then click the button

### Data Privacy
- Your audio file is uploaded to Microsoft's servers for processing
- Microsoft may retain your data according to their privacy policy
- For sensitive content, consider using Function 2a (Whisper) for local processing

### File Organization
- Keep all files for one interview in the same output directory
- Use the exact filenames shown in the instructions
- This ensures Function 4 can find the JSON file when generating outputs

## Common Issues

### Transcribe Feature Not Available
**Problem**: The Transcribe option doesn't appear in Word Online  
**Solution**: This feature requires a Microsoft 365 subscription. Check your account status.

### Upload Fails
**Problem**: Audio file won't upload to Word Online  
**Solution**:
- Check file size - Word Online has upload limits
- Ensure file is MP3 format
- Check your internet connection
- Try refreshing the page

### Transcription Quality Issues
**Problem**: Transcription has many errors  
**Solution**:
- Check audio quality (reduce background noise)
- Ensure clear speech without excessive overlap
- Edit the transcription manually in Word before saving
- For better quality, try Function 2a (Whisper)

### JSON Formatting Errors
**Problem**: Function 4 fails to read your JSON  
**Solution**:
- Use a JSON validator (jsonlint.com) to check formatting
- Ensure all strings are in quotes
- Check for proper comma placement
- Don't include trailing commas
- Match the example structure exactly

## Tips for Best Results

1. **Use good audio quality** - Clear speech, minimal background noise
2. **Edit in Word** - Fix all errors before saving the DOCX
3. **Be precise with names** - Ensure consistent speaker naming
4. **Validate JSON** - Use an online JSON validator before using Function 4
5. **Save incrementally** - Don't lose work if browser crashes

## Expected Results

After completing all steps:
- DOCX file in output directory with corrected transcript
- JSON file with properly formatted segments and speaker labels
- Ready to run Function 4 to generate TXT and VTT outputs

Example completion log:
```
📝 Displayed MS Word Online instructions for: interview.mp3
Follow the instructions to transcribe with MS Word Online
```

## Alternative

If you don't have a Microsoft 365 subscription or prefer automated transcription:
- Use **Function 2a: Transcribe MP3 using Whisper** instead
- Function 2a is free, runs entirely locally, and automatically creates the JSON file
- No manual JSON creation required
