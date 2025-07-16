# Newear Project Plan

## Overview
A CLI tool for real-time system audio captioning using local transcription models.

## Architecture Decisions

### 1. Project Management
- **pyproject.toml**: Modern Python packaging standard with Poetry support
- **Dependency management**: Poetry for development, pip-installable for users
- **Entry point**: CLI command `newear` installed via pip
- **Target**: macOS first (Apple Silicon + Intel support)

### 2. Local Transcription Models

#### Chosen: faster-whisper (Whisper.cpp Python bindings)
- **Pros**: Fast C++ implementation, small models, optimized for Apple Silicon
- **Models**: tiny (39MB), base (74MB), small (244MB)
- **Performance**: ~10x faster than openai-whisper on M1/M2 Macs
- **Library**: `faster-whisper`

### 3. Audio Capture Strategy (macOS-focused)

#### macOS System Audio Capture:
- **Primary**: BlackHole virtual audio device (free, reliable)
- **Library**: `sounddevice` for audio capture
- **Setup**: Multi-output device combining BlackHole + built-in output
- **Fallback**: Aggregate device if multi-output fails

### 4. Real-time Processing
- **Chunked processing**: 1-3 second audio chunks
- **Streaming buffer**: Rolling buffer for continuous audio
- **Threading**: Separate threads for capture/transcription/display
- **Latency target**: <2 seconds end-to-end

## Project Structure

```
newear/
├── pyproject.toml
├── README.md
├── src/
│   └── newear/
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── audio/
│       │   ├── __init__.py
│       │   ├── capture.py       # Audio capture logic
│       │   └── devices.py       # Device detection
│       ├── transcription/
│       │   ├── __init__.py
│       │   ├── whisper_local.py # Local Whisper implementation
│       │   └── models.py        # Model management
│       ├── output/
│       │   ├── __init__.py
│       │   ├── display.py       # Terminal display
│       │   └── file_writer.py   # File output
│       └── utils/
│           ├── __init__.py
│           └── config.py        # Configuration
├── tests/
│   └── test_*.py
└── models/                      # Local model storage
    └── .gitkeep
```

## Implementation Plan

### Phase 1: Core Setup
1. Create pyproject.toml with Poetry configuration
2. Set up basic CLI structure with Click/argparse
3. Implement basic audio capture with sounddevice
4. Add simple file output

### Phase 2: Transcription
1. Integrate faster-whisper for local inference
2. Implement chunked audio processing
3. Add model download/management
4. Optimize for real-time performance

### Phase 3: Polish
1. Add rich terminal UI with live updates
2. Implement configuration file support

## Key Features

### MVP Features
- [x] Real-time system audio capture
- [x] Local speech-to-text transcription
- [x] Live terminal display
- [x] Save transcripts to file
- [x] Cross-platform support

### Advanced Features
- [ ] Multiple output formats (JSON, SRT, TXT)
- [ ] Confidence scoring
- [ ] Language detection
- [ ] Noise filtering
- [ ] Custom model support

## Technical Considerations

### Performance
- **Model size vs accuracy**: Start with tiny/base models
- **Memory usage**: Efficient buffer management
- **CPU usage**: Optimize for real-time processing
- **Latency**: Minimize audio-to-text delay

### Reliability
- **Error handling**: Graceful audio device failures
- **Recovery**: Automatic reconnection on device changes
- **Logging**: Comprehensive error reporting

### User Experience
- **Setup**: Minimal configuration required
- **Feedback**: Clear status indicators
- **Documentation**: Installation guides for each OS

## Questions for Discussion

1. **Model preference**: Whisper.cpp vs Transformers vs Vosk?
2. **Audio buffer size**: How much latency is acceptable?
3. **Model management**: Auto-download vs manual installation?
4. **Configuration**: YAML/TOML config file vs CLI args only?
5. **Distribution**: PyPI package vs standalone binary?

## Next Steps

1. Review and approve this plan
2. Create pyproject.toml with chosen dependencies
3. Implement basic audio capture prototype
4. Test transcription accuracy with different models
5. Build CLI interface and real-time display
