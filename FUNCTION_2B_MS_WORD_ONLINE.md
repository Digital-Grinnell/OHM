# Function 2: Transcribe with MS Word Online

## Purpose
Provide step-by-step instructions for manual transcription using Microsoft Word Online's built-in Transcribe feature. This is an alternative to automated Whisper transcription that uses Microsoft's cloud-based transcription service.

**Note:** This documentation describes the MS Word Online mode of Function 2. Select this mode using the Transcription Mode radio buttons in the app.

## Requirements
- **Microsoft 365 subscription** - Required for Word Online transcription feature
- **MP3 file** - Select an MP3 file (either standalone or one created by Function 1)
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
5. **(Optional)** Enter speaker names in the 5 **Speaker Names** text fields
   - These names will be displayed in the instructions dialog
   - Names will be automatically applied when converting DOCX to JSON
   - Names are preserved exactly as entered (no uppercase conversion)
6. In the **Active Functions** dropdown, select **"2: Transcribe with Selected Mode"**
7. A dialog will appear with detailed step-by-step instructions
8. Follow the instructions to complete the transcription process

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
- Add the transcript to your document

### STEP 5: Save as DOCX
- Click the File menu in Word
- Select "Create a Copy"
- Select "Download a copy"
- Click "Download a copy" to confirm
- The file will download to your Downloads folder
- Move the downloaded DOCX file to your output directory: `~/OHW-data/<basename> - dg_<epoch>/`
- Ensure the filename matches the expected name exactly

### STEP 6: Convert to JSON
- After moving the DOCX file to the output directory, click the **"Convert to JSON"** button
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
~/OHW-data/<basename> - dg_<epoch>/
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
- Simply download the DOCX, move it to the output directory, and click the button

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
