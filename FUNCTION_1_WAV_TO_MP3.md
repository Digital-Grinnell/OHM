# Function 1: Convert WAV to MP3

## Purpose
Convert uncompressed WAV audio files to compressed MP3 format for oral history recordings, reducing file size while maintaining audio quality suitable for archival purposes.

## Requirements
- **ffmpeg** must be installed on your system
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
  - Windows: Download from https://ffmpeg.org/download.html

## Usage

1. In the **Inputs** section, click **Browse...** to select a directory containing your WAV files
2. Click **List WAV and MP3 Files** to scan the directory and all subdirectories
3. From the **Select Audio File** dropdown, choose the WAV file you want to convert
   - Files are displayed with relative paths (e.g., `subdir/file.wav`)
   - The app searches `~/OHW-data/` for an existing directory matching the file's basename
   - If found, it reuses that directory and epoch timestamp
   - If not found, it creates a new directory named `<basename> - dg_<epoch>`
4. In the **Active Functions** dropdown, select **"🎵 1: Convert WAV to MP3"**
5. The function will:
   - Copy the source WAV to the output directory as `dg_<epoch>.wav` (if not already copied)
   - Convert the copied WAV to `dg_<epoch>.mp3` (if MP3 doesn't already exist)
6. Monitor the status and log output for progress

## Output Directory

When you select a file for processing, OHW searches for an existing output directory in `~/OHW-data/` that matches the file's basename. If found, it reuses that directory and its epoch timestamp. If not found, it creates a new unique subdirectory with the naming pattern:

```
<filename-without-extension> - dg_<unix-timestamp>
```

For example, selecting `interview_john_doe.wav` for the first time might create:
```
~/OHW-data/interview_john_doe - dg_1712345678/
```

If you select `interview_john_doe.wav` or `interview_john_doe.mp3` again later, the app will find and reuse the existing `interview_john_doe - dg_1712345678/` directory instead of creating a new one.

The converted files will use the directory's epoch timestamp:
```
~/OHW-data/interview_john_doe - dg_1712345678/dg_1712345678.wav (copied from source)
~/OHW-data/interview_john_doe - dg_1712345678/dg_1712345678.mp3 (converted)
```

All output files for this audio file will be stored in this directory. The source WAV file is copied to the output directory with standardized naming before conversion. This keeps each oral history recording's outputs organized and allows you to work with the same file multiple times without creating duplicate directories.

## Technical Details

### Encoding Settings
- **Codec**: libmp3lame (LAME MP3 encoder)
- **Quality**: VBR (Variable Bit Rate) quality level 2
- **Average Bitrate**: ~190 kbps
- **Sample Rate**: 44100 Hz (44.1 kHz)

### File Handling
- When a file is selected, the app searches for an existing output directory matching the basename
- If found, that directory and its epoch are reused; if not, a new directory is created
- Source WAV file is copied to the output directory under `~/OHW-data/` as `dg_<epoch>.wav`
- Original source WAV file remains unchanged in its original location
- If `dg_<epoch>.wav` already exists in the output directory, the copy step is skipped
- MP3 is created from the copied WAV file in the output directory as `dg_<epoch>.mp3`
- If `dg_<epoch>.mp3` already exists in the output directory, conversion is skipped
- Selecting the same file multiple times reuses the same output directory

## Expected Results

A successful conversion will:
- Copy the source WAV to the output directory as `dg_<epoch>.wav` (if not already present)
- Create an MP3 file named `dg_<epoch>.mp3` in the unique output directory under `~/OHW-data/`
- Display file sizes for both source WAV, copied WAV, and MP3 files
- Show compression ratio (typically 10:1 or better comparing WAV to MP3)
- Log the copy and conversion details with output location
- Keep the original source WAV file unmodified in its original location

## Common Issues

### No file selected
**Problem**: Function executed without selecting a file
**Solution**: Use the Inputs section to select a directory and choose a file from the dropdown

### Not a WAV file
**Problem**: Selected file is an MP3 or other format
**Solution**: Only WAV files can be converted. Select a file with .wav extension

### ffmpeg not found
**Problem**: The system cannot find the ffmpeg executable
**Solution**: Install ffmpeg using the appropriate method for your operating system

### WAV file already copied
**Problem**: The WAV file `dg_<epoch>.wav` already exists in the output directory
**Result**: Copy step is skipped; conversion proceeds using the existing copied WAV file
**Note**: This is expected behavior and not an error

### Output file already exists
**Problem**: An MP3 file named `dg_<epoch>.mp3` already exists in the output directory
**Solution**: 
- This is expected if you've already converted this file - the app will skip the conversion
- To reconvert, manually delete the existing WAV/MP3 files in the output directory
- Note: Selecting the same file again will reuse the same output directory

### Conversion timeout
**Problem**: Conversion takes longer than 10 minutes
**Solution**: Check that the WAV file is not corrupted and that system resources are available

## Notes
- Large WAV files may take time to copy and several minutes to convert
- The conversion is CPU-intensive; other applications may slow down temporarily
- Converted files are suitable for Digital.Grinnell oral history ingestion workflows
- The selected directory is remembered between sessions
- Output directories are reused when selecting files with the same basename
- This allows you to work with the same oral history file across multiple sessions
- All processing outputs for a single audio file are kept together in its output directory
- The source WAV is preserved in both its original location and copied to the output directory
- If WAV and MP3 already exist in output directory, both copy and conversion steps are skipped
