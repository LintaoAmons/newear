#!/usr/bin/env python3
"""Test script for OpenAI translation hook."""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from newear.hooks.factory import HookFactory
from newear.hooks.manager import HookManager


# Mock transcription result
class MockTranscriptionResult:
    def __init__(self, text, confidence, start_time=None, end_time=None):
        self.text = text
        self.confidence = confidence
        self.start_time = start_time or time.time()
        self.end_time = end_time or (self.start_time + 3.0)


def test_openai_translation_hook():
    """Test the OpenAI translation hook."""
    print("🚀 Testing OpenAI Translation Hook")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found!")
        print("💡 Set your API key: export OPENAI_API_KEY=your_key_here")
        return False
    
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    # Test hook configuration
    hook_config = {
        'type': 'openai_translation',
        'enabled': True,
        'config': {
            'api_key': api_key,
            'target_language': 'Chinese',
            'model': 'gpt-3.5-turbo',
            'max_tokens': 1000,
            'temperature': 0.3,
            'print_translation': True
        }
    }
    
    print(f"📝 Hook configuration: {hook_config['config']['target_language']} translation")
    
    # Create hook
    try:
        hook = HookFactory.create_hook(hook_config)
        print(f"✅ Hook created: {hook.name}")
    except Exception as e:
        print(f"❌ Failed to create hook: {e}")
        return False
    
    # Test data
    test_texts = [
        "Hello world, this is a test",
        "How are you doing today?",
        "The weather is nice today",
        "I love programming with Python",
        "This is a real-time transcription system"
    ]
    
    print(f"\n🧪 Testing translation with {len(test_texts)} samples...")
    print("-" * 40)
    
    # Initialize hook manager
    hook_manager = HookManager()
    hook_manager.register_hook(hook)
    
    success_count = 0
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📖 Test {i}: {text}")
        
        # Create mock result
        result = MockTranscriptionResult(
            text=text,
            confidence=0.95
        )
        
        # Execute hook
        try:
            context = hook_manager.create_context(result)
            hook_results = hook_manager.execute_hooks(context)
            
            for hook_result in hook_results:
                if hook_result.success:
                    print(f"✅ Translation successful!")
                    if hook_result.data:
                        original = hook_result.data.get('original', '')
                        translated = hook_result.data.get('translated', '')
                        model = hook_result.data.get('model', '')
                        usage = hook_result.data.get('usage', {})
                        
                        print(f"   Original: {original}")
                        print(f"   Translated: {translated}")
                        print(f"   Model: {model}")
                        if usage:
                            print(f"   Usage: {usage}")
                    success_count += 1
                else:
                    print(f"❌ Translation failed: {hook_result.error}")
                    
        except Exception as e:
            print(f"❌ Hook execution failed: {e}")
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    print(f"\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{len(test_texts)} translations successful")
    
    if success_count == len(test_texts):
        print("🎉 All tests passed! OpenAI translation hook is working correctly.")
        print("\n🚀 Ready to use with newear:")
        print("   export OPENAI_API_KEY=your_key_here")
        print("   uv run newear --config config-openai-translation.yaml")
        return True
    else:
        print(f"⚠️  {len(test_texts) - success_count} tests failed")
        return False


if __name__ == '__main__':
    success = test_openai_translation_hook()
    sys.exit(0 if success else 1)