# Newear 🎧

> Vibe with ClaudeCode

A fully local and free real-time system audio captioning CLI tool for macOS using local transcription models.

## Overview

Newear is a versatile, fully local and free audio transcription tool that provides both real-time system audio captioning and batch processing of video/audio files using local Whisper models. Perfect for:

- **Live captioning** of videos, meetings, or streaming audio content
- **Video/audio file transcription** - process existing recordings, lectures, meetings
- **Accessibility support** for hearing-impaired users
- **Creating transcripts** from any audio source (live or recorded)
- **Real-time translation workflows** with multiple output formats

## Features

- 🎵 **Real-time system audio capture** using BlackHole virtual audio device
- 🎬 **Video/audio file transcription** - process MP4, AVI, MOV, MP3, WAV, and more
- 🧠 **100% local transcription** with faster-whisper (no internet required, completely free)
- 📝 **Live terminal display** with rich formatting and progress tracking
- 💾 **Multiple output formats** - TXT, JSON, SRT, VTT, CSV with timestamps
- 🖥️ **macOS optimized** with Apple Silicon support
- ⚡ **Fast performance** (~10x faster than regular Whisper)
- 🔧 **Flexible configuration** - YAML/TOML configs with CLI overrides

## Installation

### Prerequisites

1. **Python 3.9+** (recommended: use pyenv or system Python)
2. **uv** - Fast Python package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Install Newear

```bash
# Clone the repository
git clone https://github.com/yourusername/newear.git
cd newear

# Create virtual environment using uv
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install in development mode
uv pip install -e .
```


## Usage

### 1. Live Caption Transcription

Real-time system audio capture and transcription using BlackHole virtual audio device. Perfect for live captioning of videos, meetings, or any audio content playing on your Mac.

#### Prerequisites for Live Captioning

For live captioning, you need to install BlackHole virtual audio device and configure audio routing:

**Install BlackHole:**
```bash
brew install blackhole-2ch
```

**Configure Audio Routing:**

1. **Open Audio MIDI Setup**:
   - Press `Cmd + Space` and search for "Audio MIDI Setup"
   - Or go to Applications → Utilities → Audio MIDI Setup

2. **Create a Multi-Output Device**:
   - Click the `+` button in the bottom left
   - Select "Create Multi-Output Device"
   - Name it "System + BlackHole"

3. **Configure the Multi-Output Device**:
   - Check both your main speakers/headphones AND "BlackHole 2ch"
   - Set your main speakers as "Master Device" (right-click → "Use This Device As Master")
   - Ensure both devices have the same sample rate (44.1kHz or 48kHz)

4. **Set as System Output**:
   - Go to System Preferences → Sound → Output
   - Select "System + BlackHole" as your output device
   - You should still hear audio normally

**Test Audio Capture:**

Before using live captioning, test that your audio routing is working correctly:

```bash
python test_audio.py
```

This will:
- List all available audio devices
- Test audio capture for 10 seconds
- Show a clear conclusion about whether your setup is working
- Provide troubleshooting steps if there are issues

**Expected results:**
- ✅ "BlackHole 2ch" should appear in the device list
- ✅ Audio capture test should show "SUCCESSFUL" after 10 seconds
- ✅ RMS levels should be > 0 when audio is playing

#### Live Captioning Commands

```bash
# Start live captioning (auto-creates newear-YYYYMMDD_HHMMSS.txt files)
newear

# Use specific model size
newear --model tiny    # Fastest, lower accuracy
newear --model base    # Balanced (default)
newear --model small   # Better accuracy, slower

# Save transcript to specific file (creates both transcript.txt and transcript.continuous.txt)
newear --output transcript.txt

# Show timestamps in output file
newear --timestamps --output transcript.txt

# Show confidence scores in console (hidden by default)
newear --confidence --output transcript.txt
```

### 2. Video/Audio File Transcription

Process existing video and audio files directly. This is perfect for transcribing recordings, meetings, lectures, or any media files you already have.

#### Quick Start

```bash
# Transcribe any video or audio file
newear transcribe your-file.mp4

# The command will:
# 1. Detect the file type automatically
# 2. Extract audio from video files (if needed)
# 3. Show progress with estimated completion time
# 4. Create transcription files with timestamps
```

#### Step-by-Step Instructions

1. **Install ffmpeg (required for video files):**
   ```bash
   brew install ffmpeg
   ```

2. **Basic transcription:**
   ```bash
   # Transcribe a video file (creates video.txt and video.continuous.txt)
   newear transcribe video.mp4
   
   # Transcribe an audio file
   newear transcribe audio.wav
   ```

3. **Choose your model for accuracy vs speed:**
   ```bash
   # Fast transcription (good for long files)
   newear transcribe --model tiny long-recording.mp4
   
   # Balanced accuracy and speed (recommended)
   newear transcribe --model base meeting.mp4
   
   # High accuracy (best for important content)
   newear transcribe --model large interview.mp4
   ```

4. **Custom output file:**
   ```bash
   # Specify output filename
   newear transcribe --output meeting-notes.txt meeting.mp4
   
   # Output files created:
   # - meeting-notes.txt (timestamped transcript)
   # - meeting-notes.continuous.txt (single line text)
   ```

5. **Generate multiple formats:**
   ```bash
   # Create subtitle files for video editing
   newear transcribe --formats txt,srt,vtt video.mp4
   
   # Create all available formats
   newear transcribe --formats txt,json,srt,vtt,csv presentation.mp4
   ```

6. **Specify language for better accuracy:**
   ```bash
   # English content
   newear transcribe --language en presentation.mp4
   
   # Spanish content
   newear transcribe --language es conferencia.mp4
   
   # Auto-detect language (default)
   newear transcribe video.mp4
   ```

#### Supported File Formats

**Audio Files:**
- **MP3** - Most common audio format
- **WAV** - Uncompressed audio, best quality
- **FLAC** - Lossless compression
- **AAC** - Apple's audio format
- **OGG** - Open source audio format
- **M4A** - iTunes audio format
- **AIFF/AIF** - Apple's uncompressed format

**Video Files:**
- **MP4** - Most common video format
- **AVI** - Windows video format
- **MOV** - QuickTime video format
- **MKV** - Matroska video format
- **WEBM** - Web video format
- **M4V** - iTunes video format

#### Command Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output file path | `--output transcript.txt` |
| `--model` | `-m` | Whisper model size | `--model large` |
| `--language` | `-l` | Language code | `--language en` |
| `--formats` | | Output formats | `--formats txt,json,srt` |
| `--config` | | Configuration file | `--config my-config.yaml` |
| `--log-level` | | Logging verbosity | `--log-level DEBUG` |

#### Real-World Examples

**Meeting Transcription:**
```bash
# High-accuracy transcription for important meetings
newear transcribe --model medium --language en --formats txt,json --output meeting-2024-07-16.txt zoom-meeting.mp4
```

**Lecture Processing:**
```bash
# Process a lecture with subtitle generation
newear transcribe --model base --formats txt,srt,vtt --output lecture-notes.txt lecture-recording.mp4
```

**Batch Processing Multiple Files:**
```bash
# Process multiple files (basic shell loop)
for file in *.mp4; do
    newear transcribe --model small --output "${file%.*}.txt" "$file"
done
```

**Using Configuration Files:**
```bash
# Use advanced configuration for professional transcription
newear transcribe --config config-advanced-example.yaml important-presentation.mp4
```

#### What Happens During Transcription

1. **File Analysis**: Newear detects the file type and duration
2. **Audio Extraction** (for video): Audio is extracted to a temporary file
3. **Model Loading**: The specified Whisper model is loaded
4. **Progress Tracking**: Real-time progress bar with time estimates
5. **Segmentation**: Audio is processed in segments for better accuracy
6. **Output Generation**: Multiple format files are created simultaneously
7. **Cleanup**: Temporary files are automatically removed

#### Output Files Created

When you run `newear transcribe meeting.mp4`, you get:

```
meeting.txt                    # Timestamped transcript
meeting.continuous.txt         # Single line text (no timestamps)
meeting.json                   # Structured data with confidence scores
meeting.srt                    # Subtitle file for video editing
meeting.vtt                    # WebVTT subtitles for web
meeting.csv                    # Spreadsheet format for analysis
```

#### Tips for Best Results

1. **Choose the right model:**
   - `tiny`: 39MB, ~32x realtime - Good for quick testing
   - `base`: 74MB, ~16x realtime - Balanced choice (recommended)
   - `small`: 244MB, ~6x realtime - Better accuracy
   - `medium`: 769MB, ~2x realtime - High accuracy for English
   - `large`: 1550MB, ~1x realtime - Best accuracy, multilingual

2. **Specify language when known:**
   ```bash
   newear transcribe --language en video.mp4  # Faster and more accurate
   ```

3. **Use configuration files for consistent settings:**
   ```bash
   # Create a transcription config
   newear config create --output ~/.newear/transcribe.yaml
   # Edit the file to set your preferred model, formats, etc.
   newear transcribe --config ~/.newear/transcribe.yaml file.mp4
   ```

4. **Check file quality:**
   - Clear audio produces better results
   - Reduce background noise if possible
   - Ensure good recording volume levels

#### Troubleshooting

**Error: "ffmpeg not found"**
```bash
# Install ffmpeg
brew install ffmpeg

# Verify installation
ffmpeg -version
```

**Error: "Unsupported file format"**
- Check that your file has a supported extension
- Convert the file to a supported format:
  ```bash
  ffmpeg -i input.xyz -c:a libmp3lame output.mp3
  ```

**Poor transcription quality:**
- Try a larger model: `--model medium` or `--model large`
- Specify the language: `--language en`
- Check audio quality in the original file

**Large files taking too long:**
- Use a smaller model: `--model tiny` or `--model base`
- Consider splitting large files into smaller segments

### Model Download

**Models are downloaded automatically on first use** - no manual setup required!

```bash
# First time running with 'base' model
newear --model base --output transcript.txt
```

**What happens:**

1. faster-whisper checks if the model exists locally
2. If not found, it automatically downloads from Hugging Face
3. Model is cached for future use
4. Transcription begins once download completes

**Download sizes and times:**
| Model | Size | Use Case |
|-------|------|----------|
| tiny | 39MB | Testing, very fast |
| base | 74MB | General use (recommended) |
| small | 244MB | Higher accuracy |
| medium | 769MB | Best accuracy (English) |
| large | 1550MB | Maximum accuracy (bilingual support)|
| large-v2 | 1550MB | Maximum accuracy (bilingual support) |

**First run vs subsequent runs:**

```bash
# First run - downloads model (one-time)
newear --model tiny --output test.txt
# Loading Whisper model: tiny
# Downloading model... (downloads 39MB)
# Model loaded successfully

# Second run - uses cached model (instant)
newear --model tiny --output test2.txt
# Loading Whisper model: tiny
# Model loaded successfully (instant)
```

**Requirements:**

- **First use**: Internet connection required for download
- **Subsequent uses**: Works offline with cached models
- **Storage**: Models cached in `~/.cache/huggingface/hub/`

### Manual Model Download (Optional)

If you prefer to download models manually or work in offline environments:

#### Step 1: Install huggingface-hub

```bash
pip install huggingface-hub
```

#### Step 2: Download Models Manually

```bash
# Download specific models
huggingface-cli download Systran/faster-whisper-tiny
huggingface-cli download Systran/faster-whisper-base
huggingface-cli download Systran/faster-whisper-small
huggingface-cli download Systran/faster-whisper-medium
huggingface-cli download Systran/faster-whisper-large-v2

# Or download all models with a script
python -c "
from huggingface_hub import snapshot_download
models = ['large-v2']
for model in models:
    print(f'Downloading {model}...')
    snapshot_download(repo_id=f'Systran/faster-whisper-{model}')
    print(f'✅ {model} downloaded')
"
```

#### Step 3: Use Downloaded Models

```bash
# Models are automatically used from cache
newear --model base --output transcript.txt

# Or force offline mode (no internet check)
export HF_HUB_OFFLINE=1
newear --model base --output transcript.txt
```

#### Custom Cache Location

```bash
# Set custom download directory
export HF_HOME=/path/to/your/models
export HUGGINGFACE_HUB_CACHE=/path/to/your/models

# Download to custom location
huggingface-cli download Systran/faster-whisper-base

# Use from custom location
newear --model base
```

#### Verify Downloaded Models

```bash
# Check what models are cached
ls -la ~/.cache/huggingface/hub/

# Check cache size
du -sh ~/.cache/huggingface/hub/

# List downloaded models
python -c "
import os
from pathlib import Path
cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
models = [d.name for d in cache_dir.iterdir() if d.name.startswith('models--Systran--faster-whisper')]
print('Downloaded models:')
for model in sorted(models):
    size = sum(f.stat().st_size for f in (cache_dir / model).rglob('*') if f.is_file())
    print(f'  {model.split(\"--\")[-1]}: {size / 1024 / 1024:.1f} MB')
"
```

#### Completely Offline Usage

```bash
# After manual download, work completely offline
export HF_HUB_OFFLINE=1
newear --model base --output transcript.txt
```

This will use only locally cached models without any internet connection.

### Optimizing Chunk Duration for Better Accuracy

**Chunk duration significantly affects transcription confidence and accuracy:**

```bash
# Fast but lower accuracy (good for testing)
newear --chunk-duration 2.0 --model tiny

# Balanced accuracy and latency (default)
newear --chunk-duration 5.0 --model base

# Higher accuracy, slight delay
newear --chunk-duration 8.0 --model small

# Maximum accuracy for complex speech
newear --chunk-duration 10.0 --model medium
```

**Chunk Duration Guidelines:**

| Duration | Latency  | Accuracy | Use Case                          |
| -------- | -------- | -------- | --------------------------------- |
| 1-2s     | Very low | Lower    | Testing, simple speech            |
| 3-5s     | Low      | Good     | General use (default: 5s)         |
| 5-8s     | Medium   | High     | Complex speech, technical content |
| 8-10s    | High     | Highest  | Maximum accuracy, presentations   |

**Why longer chunks are better:**

- **More context** for the AI model to understand speech
- **Better sentence boundaries** detection
- **Higher confidence scores** due to complete phrases
- **Reduced word fragmentation** in mid-sentence

**Trade-offs:**

- **Longer chunks** = Higher accuracy but more latency
- **Shorter chunks** = Lower latency but reduced confidence
- **Sweet spot** = 5-8 seconds for most use cases

### Output Options

**Console Output:**

```bash
# Default - Clean text only (no confidence scores)
newear --output transcript.txt
> Hello, this is a test transcription.
> The audio quality is working well.

# With confidence scores (opt-in)
newear --confidence --output transcript.txt
> Hello, this is a test transcription. (confidence: 0.95)
> The audio quality is working well. (confidence: 0.87)
```

**File Output:**
Newear always creates transcript files. When using `--output filename.txt`, it creates two files:

1. **`filename.txt`** - Timestamped transcript (default format)

   ```
   [2024-07-16 15:30:15] Hello, this is a test transcription.
   [2024-07-16 15:30:18] The audio quality is working well.
   ```

2. **`filename.continuous.txt`** - Continuous one-liner (no line breaks)
   ```
   Hello, this is a test transcription. The audio quality is working well.
   ```

**Output Format Use Cases:**

- **Timestamped file**: Meeting notes, analysis, debugging
- **Continuous file**: Text processing, ML training, simple copy-paste
- **Console output**: Real-time monitoring, clean display
- **Confidence scores**: Quality assessment, debugging transcription issues

### Advanced Usage

```bash
# Use specific audio device
newear --device 5

# Set custom language (auto-detect by default)
newear --language en

# Show confidence scores in console output
newear --confidence --output transcript.txt

# Rich terminal UI with live updates (default)
newear --rich-ui --model base

# Simple terminal output (no rich UI)
newear --no-rich-ui --confidence

# Multiple output formats
newear --formats txt,json,srt,vtt,csv --output meeting

# Combine options for optimal accuracy
newear --model small --chunk-duration 8.0 --confidence --output meeting.txt

# Custom audio settings
newear --sample-rate 44100 --chunk-duration 3.0
```

## Configuration

Newear supports comprehensive configuration through YAML/TOML files and CLI arguments. Configuration files provide persistent settings, while CLI arguments override them for specific runs.

### Configuration Files

Newear automatically searches for configuration files in these locations (in order):

1. `./newear.yaml` / `./newear.toml` (current directory)
2. `./.newear.yaml` / `./.newear.toml` (current directory)
3. `~/.newear/config.yaml` / `~/.newear/config.toml`
4. `~/.config/newear/config.yaml` / `~/.config/newear/config.toml`

### Quick Start with Configuration

```bash
# Create default configuration file
newear config create

# View current configuration
newear config show

# Create configuration template
newear config template

# Use custom configuration file
newear --config /path/to/custom.yaml
# or create simple link
ln -s config-minimal-example.yaml newear.yaml
```

### Configuration Examples

See the included example files for complete configurations:

- **`config-example.yaml`** - Standard balanced configuration
- **`config-advanced-example.yaml`** - High-accuracy professional setup
- **`config-minimal-example.yaml`** - Fast, lightweight configuration
- **`config-example.toml`** - TOML format alternative

#### Standard Configuration (`config-example.yaml`)

```yaml
# Audio capture settings
audio:
  sample_rate: 16000 # Optimal for speech recognition
  chunk_duration: 5.0 # Balanced accuracy vs latency
  device_index: null # Auto-detect best device

# Transcription settings
transcription:
  model_size: "base" # Good balance of speed/accuracy
  language: null # Auto-detect language
  device: "cpu" # Use CPU (or "auto" for GPU if available)

# Output settings
output:
  show_timestamps: true # Include timestamps in files
  show_confidence: false # Keep console output clean
  formats: ["txt", "continuous"] # Generate both formats

# Display settings
display:
  rich_ui: true # Use rich terminal interface
  max_lines: 6 # Compact display
  show_stats: true # Show performance stats
```

#### High-Accuracy Configuration (`config-advanced-example.yaml`)

```yaml
# Optimized for professional transcription
transcription:
  model_size: "medium" # Higher accuracy model
  language: "en" # Specify language if known
  device: "auto" # Use GPU if available
  confidence_threshold: 0.8 # Higher confidence threshold

audio:
  chunk_duration: 8.0 # Longer chunks for better context

output:
  formats: ["txt", "continuous", "json", "srt", "vtt", "csv"]
  output_dir: "~/Documents/transcripts" # Organized storage

display:
  max_lines: 8 # Show more context
  update_interval: 0.05 # Smoother updates
```

#### Minimal Configuration (`config-minimal-example.yaml`)

```yaml
# Fast, lightweight setup
transcription:
  model_size: "tiny" # Fastest model
  device: "cpu" # CPU only

audio:
  chunk_duration: 3.0 # Shorter chunks for speed

output:
  show_timestamps: false # Simple output
  formats: ["txt"] # Basic text only

display:
  rich_ui: false # Simple terminal output
  show_stats: false # No extra information
```

### Configuration Options Reference

#### Audio Settings (`audio`)

| Option           | Default | Description                             |
| ---------------- | ------- | --------------------------------------- |
| `sample_rate`    | 16000   | Audio sample rate in Hz                 |
| `channels`       | 1       | Number of audio channels                |
| `chunk_duration` | 5.0     | Audio chunk length in seconds           |
| `buffer_size`    | 4096    | Audio buffer size                       |
| `device_index`   | null    | Audio device index (null = auto-detect) |

#### Transcription Settings (`transcription`)

| Option                 | Default | Description                                     |
| ---------------------- | ------- | ----------------------------------------------- |
| `model_size`           | "base"  | Whisper model: tiny, base, small, medium, large |
| `language`             | null    | Language code (null = auto-detect)              |
| `device`               | "cpu"   | Processing device: cpu, cuda, auto              |
| `compute_type`         | "int8"  | Precision: int8, int16, float16, float32        |
| `confidence_threshold` | 0.7     | Threshold for high-confidence classification    |

#### Output Settings (`output`)

| Option            | Default               | Description                       |
| ----------------- | --------------------- | --------------------------------- |
| `show_timestamps` | true                  | Include timestamps in files       |
| `show_confidence` | false                 | Show confidence in console        |
| `auto_save`       | true                  | Automatically save transcripts    |
| `output_dir`      | null                  | Output directory (null = current) |
| `formats`         | ["txt", "continuous"] | Output formats to generate        |

#### Display Settings (`display`)

| Option            | Default | Description                          |
| ----------------- | ------- | ------------------------------------ |
| `rich_ui`         | true    | Use rich terminal interface          |
| `max_lines`       | 6       | Maximum transcript lines in terminal |
| `show_stats`      | true    | Show performance statistics          |
| `update_interval` | 0.1     | Display update frequency             |

### Output Formats

Newear supports multiple output formats for different use cases:

| Format         | Extension         | Description                     | Use Case                     |
| -------------- | ----------------- | ------------------------------- | ---------------------------- |
| **txt**        | `.txt`            | Timestamped transcript          | General use, meeting notes   |
| **continuous** | `.continuous.txt` | Single line, no timestamps      | Text processing, ML training |
| **json**       | `.json`           | Structured data with confidence | Data analysis, debugging     |
| **srt**        | `.srt`            | Subtitle format                 | Video subtitles              |
| **vtt**        | `.vtt`            | WebVTT format                   | Web video captions           |
| **csv**        | `.csv`            | Spreadsheet format              | Data analysis, Excel         |

### Configuration Management Commands

```bash
# Create default configuration
newear config create

# Create configuration in specific format
newear config create --format toml --output ~/.newear/config.toml

# Show current configuration
newear config show

# Show configuration template
newear config template

# Use custom configuration file
newear --config /path/to/custom.yaml --output meeting.txt

# Transcribe video or audio files
newear transcribe video.mp4
newear transcribe --model medium --formats txt,srt audio.wav
```

### CLI Override Examples

Configuration files provide defaults, but CLI arguments always override them:

```bash
# Use config file defaults (including UI mode)
newear

# Use minimal config with simple CLI display
newear --config config-minimal-example.yaml

# Override model size from config
newear --model medium

# Override multiple settings
newear --model small --chunk-duration 8.0 --formats txt,json,srt

# Force rich UI even if config says rich_ui: false
newear --rich-ui --config config-minimal-example.yaml

# Force simple CLI even if config says rich_ui: true
newear --no-rich-ui --confidence

# Use different output directory
newear --output ~/Documents/meeting.txt
```

### Environment Variables

You can also use environment variables for configuration:

```bash
# Set via environment
export NEWEAR_MODEL_SIZE=small
export NEWEAR_CHUNK_DURATION=8.0
export NEWEAR_LANGUAGE=en

# Use environment settings
newear --output meeting.txt
```

### Configuration Priority

Settings are applied in this order (highest to lowest priority):

1. **CLI arguments** (highest priority)
2. **Environment variables**
3. **Configuration file** (specified with `--config`)
4. **Auto-detected configuration file**
5. **Default values** (lowest priority)

This allows you to set up default preferences in a config file while easily overriding them for specific use cases.

### Output File Examples

**Example 1: Default behavior (auto-named files)**

```bash
newear --model base
```

Creates:

- `newear-20240716_153045.txt` - Timestamped entries for analysis
- `newear-20240716_153045.continuous.txt` - One-liner for processing

**Example 2: Custom filename**

```bash
newear --model base --output meeting.txt
```

Creates:

- `meeting.txt` - Timestamped entries for analysis
- `meeting.continuous.txt` - One-liner for processing

**Example 3: With confidence scores for debugging**

```bash
newear --model base --confidence --output debug.txt
```

Shows confidence in console while still creating both files.

**Example 4: High accuracy setup**

```bash
newear --model medium --chunk-duration 10.0 --language en --output presentation.txt
```

Optimized for maximum accuracy with longer chunks and specific language.

### Environment Variables

```bash
# Audio settings
export NEWEAR_SAMPLE_RATE=16000
export NEWEAR_CHUNK_DURATION=5.0
export NEWEAR_DEVICE_INDEX=5

# Transcription settings
export NEWEAR_MODEL_SIZE=base
export NEWEAR_LANGUAGE=en

# Output settings
export NEWEAR_OUTPUT_FILE=transcript.txt
export NEWEAR_SHOW_TIMESTAMPS=true
```

## Troubleshooting

### No Audio Detected

1. **Check BlackHole Installation**:

   ```bash
   brew list blackhole-2ch
   ```

2. **Verify Multi-Output Device**:

   - Open Audio MIDI Setup
   - Ensure Multi-Output Device includes BlackHole
   - Check that it's set as system output

3. **Test Audio Routing**:
   - Play some audio (music, video)
   - Run `python test_audio.py`
   - Should show RMS levels > 0

### Device Not Found

1. **List Available Devices**:

   ```bash
   python -c "from newear.audio import AudioCapture; AudioCapture().list_devices()"
   ```

2. **Look for BlackHole**:

   - Should appear as "BlackHole 2ch"
   - If not found, reinstall BlackHole

3. **Use Specific Device**:
   ```bash
   newear --device INDEX_NUMBER
   ```

### Poor Transcription Quality

1. **Use Better Model**:

   ```bash
   newear --model small  # or medium, large
   ```

2. **Check Audio Quality**:

   - Ensure clean audio input
   - Avoid background noise
   - Use higher sample rate if needed

3. **Adjust Chunk Duration**:
   ```bash
   newear --chunk-duration 8.0  # Longer chunks for better context
   ```

### Performance Issues

1. **Use Smaller Model**:

   ```bash
   newear --model tiny
   ```

2. **Reduce Chunk Duration**:

   ```bash
   newear --chunk-duration 3.0
   ```

3. **Check System Resources**:
   - Close other audio applications
   - Ensure sufficient RAM/CPU

## Technical Details

### Audio Pipeline

```
System Audio → BlackHole → Multi-Output → Speakers + Newear
```

### Processing Flow

```
Audio Capture → Chunking → Whisper Model → Text Output → File/Display
```

### Model Sizes

- **tiny**: 39MB, ~32x realtime on M1
- **base**: 74MB, ~16x realtime on M1
- **small**: 244MB, ~6x realtime on M1
- **medium**: 769MB, ~2x realtime on M1
- **large**: 1550MB, ~1x realtime on M1

## Development

### Testing Phase 1 Implementation

The Phase 1 implementation includes:

- ✅ pyproject.toml with setuptools configuration
- ✅ CLI structure with Typer
- ✅ Audio capture with sounddevice
- ✅ File output with timestamps

#### Prerequisites for Testing

```bash
# Activate virtual environment
uv venv
source .venv/bin/activate

# Install in development mode
uv pip install -e .

# Install dev dependencies
uv pip install -e ".[dev]"
```

#### Phase 1 Testing Steps

1. **Test CLI Installation**

   ```bash
   newear --help
   ```

   Expected: Help text showing all available options

2. **Test Audio Device Detection**

   ```bash
   newear --list-devices
   ```

   Expected: List of audio devices including BlackHole if installed

3. **Test Basic Audio Capture**

   ```bash
   python test_audio.py
   ```

   Expected: Device list, audio capture test with RMS levels > 0 when audio plays

4. **Test File Output**

   ```bash
   newear --output test_output.txt
   # Play some audio, then stop with Ctrl+C
   ```

   Expected: Creates test_output.txt with timestamped entries

5. **Test CLI Options**
   ```bash
   newear --timestamps --chunk-duration 1.0 --sample-rate 16000
   ```
   Expected: Runs with specified settings, shows configuration

#### Manual Testing Checklist

- [ ] CLI command installs correctly (`newear --help`)
- [ ] Audio devices are detected (`--list-devices`)
- [ ] Audio capture works with RMS levels > 0 (`test_audio.py`)
- [ ] File output creates timestamped entries (`--output file.txt`)
- [ ] Different audio settings work (`--sample-rate`, `--chunk-duration`)
- [ ] Error handling works (invalid device, no audio)
- [ ] Graceful shutdown with Ctrl+C

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/
```

### Code Formatting

```bash
# Install dev dependencies if not already installed
uv pip install -e ".[dev]"

# Format code
black src/
isort src/
```

### Building

```bash
uv pip install build
python -m build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/newear/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/newear/discussions)
- 📧 **Email**: your.email@example.com

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the transcription model
- [BlackHole](https://github.com/ExistentialAudio/BlackHole) for virtual audio routing
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) for optimized inference
