# Phase 1 Implementation Guide

## Overview

Phase 1 of the Newear project implements the core foundation for real-time audio captioning. This phase focuses on basic audio capture, CLI structure, and file output - **without actual speech-to-text transcription**.

## What's Implemented in Phase 1

### ✅ Complete Features
- **pyproject.toml** - Modern Python packaging with setuptools configuration
- **CLI structure** - Typer-based command-line interface with comprehensive options
- **Audio capture** - sounddevice integration with device detection and management
- **File output** - Rich file writer with timestamps and multiple format support

### 🔄 Current Functionality
Phase 1 is an **audio level monitor** that:
- Captures system audio in real-time
- Calculates RMS (Root Mean Square) levels for audio detection
- Logs detected audio events to console and file
- Provides device management and configuration options

### ❌ Not Yet Implemented
- Speech-to-text transcription (planned for Phase 2)
- Whisper model integration (planned for Phase 2)
- Live text display (planned for Phase 3)

## Testing Phase 1

### Prerequisites
```bash
# Activate virtual environment using uv
uv venv
source .venv/bin/activate

# Install in development mode
uv pip install -e .

# Install dev dependencies
uv pip install -e ".[dev]"
```

### Testing Steps

#### 1. CLI Installation Test
```bash
newear --help
```
**Expected**: Help text showing all available options and commands

#### 2. Audio Device Detection
```bash
newear --list-devices
```
**Expected**: List of available audio devices, with BlackHole highlighted if installed

#### 3. Basic Audio Capture Test
```bash
python test_audio.py
```
**Expected**: 
- Device list display
- Audio capture test showing RMS levels > 0 when audio is playing
- Success message if audio is detected

#### 4. File Output Test
```bash
newear --output test_output.txt
```

**What happens:**
1. The command starts audio monitoring
2. **Play some audio** (music, video, etc.) while it's running
3. Press Ctrl+C to stop
4. Check the contents of `test_output.txt`

**Expected file contents:**
```
[2024-07-16 14:30:15] Audio detected: RMS = 0.002345
[2024-07-16 14:30:17] Audio detected: RMS = 0.003421
[2024-07-16 14:30:19] Audio detected: RMS = 0.001876
```

**Important notes:**
- The file will **only contain entries when audio is detected** (RMS > 0.001)
- Each line shows timestamp and RMS level of detected audio
- **No transcription text** - Phase 1 only monitors audio levels
- File will be empty if no audio is playing or RMS levels are too low
- You must have audio routed through BlackHole for detection

#### 5. CLI Options Test
```bash
newear --timestamps --chunk-duration 1.0 --sample-rate 16000
```
**Expected**: Runs with specified settings, displays configuration in console

### Manual Testing Checklist

- [ ] CLI command installs correctly (`newear --help`)
- [ ] Audio devices are detected (`newear --list-devices`)
- [ ] Audio capture works with RMS levels > 0 (`python test_audio.py`)
- [ ] File output creates timestamped entries when audio plays
- [ ] Different audio settings work (`--sample-rate`, `--chunk-duration`)
- [ ] Error handling works (invalid device, no audio)
- [ ] Graceful shutdown with Ctrl+C shows statistics

### Common Issues & Solutions

#### No Audio Detected
- **Problem**: File is empty or shows no RMS levels
- **Solution**: 
  1. Ensure BlackHole is installed: `brew install blackhole-2ch`
  2. Create Multi-Output Device in Audio MIDI Setup
  3. Set Multi-Output Device as system output
  4. Play audio while running the command

#### Device Not Found
- **Problem**: Error about audio device not found
- **Solution**:
  1. Run `newear --list-devices` to see available devices
  2. Use specific device: `newear --device INDEX_NUMBER`
  3. Check BlackHole installation

#### Permission Errors
- **Problem**: Cannot access audio device
- **Solution**: Grant microphone permissions in System Preferences > Privacy

## What Phase 1 Demonstrates

1. **Audio Pipeline**: System Audio → BlackHole → Multi-Output → Speakers + Newear
2. **CLI Interface**: Complete command-line interface with all future options
3. **File Output**: Timestamped logging system ready for transcription data
4. **Device Management**: Audio device detection and configuration
5. **Error Handling**: Graceful error handling and user feedback

## Next Steps (Phase 2)

Phase 2 will add:
- faster-whisper integration for local speech-to-text
- Chunked audio processing for real-time transcription
- Model download and management
- Replace RMS logging with actual transcription text

## File Structure

```
newear/
├── src/newear/
│   ├── main.py              # CLI entry point ✅
│   ├── audio/
│   │   ├── capture.py       # Audio capture logic ✅
│   │   └── devices.py       # Device detection ✅
│   ├── output/
│   │   └── file_writer.py   # File output ✅
│   └── utils/
│       └── config.py        # Configuration ✅
├── test_audio.py            # Audio testing script ✅
└── pyproject.toml           # Project configuration ✅
```

## Summary

Phase 1 successfully implements the foundation for real-time audio captioning. While it doesn't yet perform speech-to-text transcription, it demonstrates that the audio pipeline, CLI interface, and file output systems are working correctly. The RMS level monitoring proves that audio is being captured and processed in real-time, setting the stage for Phase 2's transcription features.