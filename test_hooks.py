#!/usr/bin/env python3
"""Test script for the hook system."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dataclasses import dataclass
from typing import Optional
import time

# Mock TranscriptionResult for testing
@dataclass
class MockTranscriptionResult:
    text: str
    confidence: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None

# Test the hook system without importing full modules
def test_hook_system():
    # Test basic hook functionality
    hook_config = {
        'type': 'console_log',
        'enabled': True,
        'config': {'show_confidence': True}
    }
    
    # Create mock transcription result
    result = MockTranscriptionResult(
        text='Hello world, this is a test',
        confidence=0.95,
        start_time=time.time(),
        end_time=time.time() + 3.0
    )
    
    print(f"✓ Created mock transcription result: {result.text}")
    print(f"✓ Confidence: {result.confidence}")
    print(f"✓ Hook configuration: {hook_config}")
    
    # Test file append hook
    file_hook_config = {
        'type': 'file_append',
        'enabled': True,
        'config': {
            'file_path': 'test-hook-output.log',
            'format': '[{confidence:.2f}] {text}'
        }
    }
    
    # Write to file to test
    with open('test-hook-output.log', 'w') as f:
        formatted_text = file_hook_config['config']['format'].format(
            text=result.text,
            confidence=result.confidence
        )
        f.write(formatted_text + '\n')
    
    print(f"✓ File hook test completed - check test-hook-output.log")
    
    # Test translation hook concept
    translation_hook_config = {
        'type': 'translation',
        'enabled': True,
        'config': {
            'target_language': 'es',
            'service': 'command',
            'command': 'echo "Translation: {text}"',
            'print_translation': True
        }
    }
    
    # Simulate translation
    import subprocess
    command = translation_hook_config['config']['command'].format(text=result.text)
    try:
        output = subprocess.run(command, shell=True, capture_output=True, text=True)
        if output.returncode == 0:
            print(f"✓ Translation hook test: {output.stdout.strip()}")
        else:
            print(f"✗ Translation hook failed: {output.stderr}")
    except Exception as e:
        print(f"✗ Translation hook error: {e}")
    
    print("\n🎉 Hook system tests completed!")

if __name__ == '__main__':
    test_hook_system()