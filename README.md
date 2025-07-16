# Newear 🎧

Real-time system audio captioning CLI tool for macOS using local transcription models.

## Overview

Newear captures your system audio in real-time and provides live transcription using local Whisper models. Perfect for:
- Live captioning of videos, meetings, or audio content
- Accessibility support for hearing-impaired users
- Creating transcripts of audio content
- Real-time translation workflows

## Features

- 🎵 **Real-time system audio capture** using BlackHole virtual audio device
- 🧠 **Local transcription** with faster-whisper (no internet required)
- 📝 **Live terminal display** with rich formatting
- 💾 **Save transcripts** to file with timestamps
- 🖥️ **macOS optimized** with Apple Silicon support
- ⚡ **Fast performance** (~10x faster than regular Whisper)

## Installation

### Prerequisites

1. **Python 3.9+** (recommended: use pyenv or system Python)
2. **uv** - Fast Python package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. **Homebrew** for installing BlackHole

### Step 1: Install BlackHole Virtual Audio Device

BlackHole is a free virtual audio device that allows capturing system audio:

```bash
brew install blackhole-2ch
```

### Step 2: Configure Audio Routing

After installing BlackHole, you need to route your system audio through it:

#### Using Audio MIDI Setup

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

### Step 3: Install Newear

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

### Step 4: Test Audio Capture

Run the test script to verify everything is working:

```bash
python test_audio.py
```

You should see:
- List of available audio devices
- "BlackHole 2ch" in the device list
- Audio capture test with RMS levels > 0 when audio is playing

## Usage

### Basic Usage

```bash
# Start live captioning
newear

# Use specific model size
newear --model tiny    # Fastest, lower accuracy
newear --model base    # Balanced (default)
newear --model small   # Better accuracy, slower

# Save transcript to file
newear --output transcript.txt

# Show timestamps
newear --timestamps
```

### Advanced Usage

```bash
# Use specific audio device
newear --device 5

# Set custom language (auto-detect by default)
newear --language en

# Custom audio settings
newear --sample-rate 44100 --chunk-duration 2.0
```

### Environment Variables

```bash
# Audio settings
export NEWEAR_SAMPLE_RATE=16000
export NEWEAR_CHUNK_DURATION=3.0
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
   newear --chunk-duration 5.0  # Longer chunks for better context
   ```

### Performance Issues

1. **Use Smaller Model**:
   ```bash
   newear --model tiny
   ```

2. **Reduce Chunk Duration**:
   ```bash
   newear --chunk-duration 2.0
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
