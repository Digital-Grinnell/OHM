# Function 6: Edit Review Notes

## Purpose
Create or edit a `review_notes.md` file for the currently selected oral history. Use this to record reviewer observations, corrections, follow-up questions, or any other notes associated with the recording and its transcript.

## Requirements
- **Audio file selected**: Must have selected a file from the dropdown in the Inputs section
- **Output directory present**: The per-file output directory must exist (created automatically when a file is selected)

## Usage

1. Select an audio file from the **Select Audio File** dropdown in the Inputs section
2. In the **Active Functions** dropdown, select **"📋 6: Edit Review Notes"**
3. A Markdown editor dialog will open:
   - If `review_notes.md` already exists in the output directory, its current content is loaded into the editor
   - If no file exists yet, a starter template is pre-filled with the filename and today's date
4. Write or edit your notes using standard Markdown syntax
5. Click **Save** to write the file and close the dialog, or **Cancel** to discard changes

## Notes File Location

The file is saved inside the per-file output directory alongside all other deliverables:

```
<working_dir>/OHM-data/<sanitized-basename>--dg_<epoch>/review_notes.md
```

Example:
```
/Volumes/recordings/OHM-data/Darrell_Hall--dg_1775499960/review_notes.md
```

## Starter Template

When no `review_notes.md` exists yet, the editor opens with this template:

```markdown
# Review Notes
**File:** Darrell Hall.wav
**Date:** April 13, 2026

## Notes

_Enter your review notes here._
```

You can replace or extend any part of the template before saving.

## Markdown Tips

The file is plain Markdown, so you can use standard formatting:

```markdown
# Headings
## Sub-headings

**Bold text**  
_Italic text_

- Bullet item
- Another item

1. Numbered list
2. Second item

> Block quote for verbatim corrections

[Link text](https://example.com)
```

## Suggested Note Sections

Feel free to organise notes however suits your project. Some common sections:

### Audio Quality
Note any audio issues (background noise, low volume, cross-talk) that may have affected transcription accuracy.

### Speaker Identification
Record how speakers were identified and any uncertainty in speaker attribution.

### Transcription Corrections
List significant corrections made to the auto-generated transcript.

### Follow-up Items
Questions or action items that arose during review (e.g., clarify a date, verify a proper noun, obtain consent).

### Archival Notes
Contextual information for future archivists: related collections, subject matter, significance.

## Behaviour Notes

- **Save** writes the file immediately and closes the dialog; any write error is shown inline and the dialog stays open
- **Cancel** closes the dialog without making any changes — the existing file (if any) is untouched
- You can run Function 3 multiple times; each save overwrites the previous content
- The file is plain UTF-8 text and can be opened and edited in any text editor outside the app

## Access During Function 2

You do not need to leave the transcription dialog to take notes. The Function 2 (MS Word Online) dialog includes a built-in **📋 Review Notes** tab that opens the same `review_notes.md` file. Click **Save Notes** inside that tab to save without closing the transcription instructions. Any notes saved there are immediately available the next time you open Function 3.
