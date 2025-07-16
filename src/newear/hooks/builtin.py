"""Built-in hooks for common post-transcription actions."""

import json
import subprocess
from typing import Dict, Any, Optional
from .manager import Hook
from .types import HookContext, HookResult


class ConsoleLogHook(Hook):
    """Hook that logs transcription results to console."""
    
    def execute(self, context: HookContext) -> HookResult:
        """Log the transcription result to console."""
        try:
            text = context.transcription_result.text.strip()
            confidence = context.transcription_result.confidence
            
            # Format the log message
            if self.config.get('show_confidence', False):
                message = f"[{confidence:.2f}] {text}"
            else:
                message = text
            
            # Log to console
            print(f"📝 {message}")
            
            return HookResult(
                success=True,
                message=f"Logged transcription: {text[:50]}..."
            )
            
        except Exception as e:
            return HookResult(
                success=False,
                error=f"Failed to log to console: {str(e)}"
            )


class FileAppendHook(Hook):
    """Hook that appends transcription results to a file."""
    
    def execute(self, context: HookContext) -> HookResult:
        """Append the transcription result to a file."""
        try:
            file_path = self.config.get('file_path', 'hooks.log')
            format_str = self.config.get('format', '{text}')
            
            text = context.transcription_result.text.strip()
            
            # Format the text
            formatted_text = format_str.format(
                text=text,
                confidence=context.transcription_result.confidence,
                chunk_index=context.chunk_index,
                timestamp=context.transcription_result.start_time
            )
            
            # Append to file
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(formatted_text + '\n')
            
            return HookResult(
                success=True,
                message=f"Appended to {file_path}",
                data={'file_path': file_path}
            )
            
        except Exception as e:
            return HookResult(
                success=False,
                error=f"Failed to append to file: {str(e)}"
            )


class CommandHook(Hook):
    """Hook that executes a shell command with transcription text."""
    
    def execute(self, context: HookContext) -> HookResult:
        """Execute a shell command with transcription text."""
        try:
            command_template = self.config.get('command', 'echo "{text}"')
            text = context.transcription_result.text.strip()
            
            # Replace placeholders in command
            command = command_template.format(
                text=text,
                confidence=context.transcription_result.confidence,
                chunk_index=context.chunk_index
            )
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.get('timeout', 30)
            )
            
            if result.returncode == 0:
                return HookResult(
                    success=True,
                    message=f"Command executed successfully",
                    data={
                        'command': command,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
                )
            else:
                return HookResult(
                    success=False,
                    error=f"Command failed with code {result.returncode}: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return HookResult(
                success=False,
                error="Command timed out"
            )
        except Exception as e:
            return HookResult(
                success=False,
                error=f"Failed to execute command: {str(e)}"
            )


class WebhookHook(Hook):
    """Hook that sends transcription results to a webhook URL."""
    
    def execute(self, context: HookContext) -> HookResult:
        """Send transcription result to webhook."""
        try:
            import requests
            
            url = self.config.get('url')
            if not url:
                return HookResult(
                    success=False,
                    error="No webhook URL configured"
                )
            
            # Prepare payload
            payload = {
                'text': context.transcription_result.text.strip(),
                'confidence': context.transcription_result.confidence,
                'chunk_index': context.chunk_index,
                'timestamp': context.transcription_result.start_time
            }
            
            # Add custom headers if configured
            headers = self.config.get('headers', {})
            headers.setdefault('Content-Type', 'application/json')
            
            # Send request
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.get('timeout', 10)
            )
            
            if response.status_code == 200:
                return HookResult(
                    success=True,
                    message=f"Webhook sent successfully",
                    data={'response': response.json() if response.headers.get('content-type') == 'application/json' else response.text}
                )
            else:
                return HookResult(
                    success=False,
                    error=f"Webhook failed with status {response.status_code}: {response.text}"
                )
                
        except ImportError:
            return HookResult(
                success=False,
                error="requests library not available for webhook hook"
            )
        except Exception as e:
            return HookResult(
                success=False,
                error=f"Failed to send webhook: {str(e)}"
            )


class TranslationHook(Hook):
    """Hook that translates transcription text using AI or translation service."""
    
    def execute(self, context: HookContext) -> HookResult:
        """Translate the transcription text."""
        try:
            text = context.transcription_result.text.strip()
            target_language = self.config.get('target_language', 'en')
            service = self.config.get('service', 'command')
            
            if service == 'command':
                # Use a command-line translation tool
                command_template = self.config.get('command', 'echo "Translation: {text}"')
                command = command_template.format(
                    text=text,
                    target_language=target_language
                )
                
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get('timeout', 30)
                )
                
                if result.returncode == 0:
                    translated_text = result.stdout.strip()
                    
                    # Log translation
                    if self.config.get('print_translation', True):
                        print(f"🌍 [{target_language}] {translated_text}")
                    
                    return HookResult(
                        success=True,
                        message=f"Translated to {target_language}",
                        data={
                            'original': text,
                            'translated': translated_text,
                            'target_language': target_language
                        }
                    )
                else:
                    return HookResult(
                        success=False,
                        error=f"Translation command failed: {result.stderr}"
                    )
            
            else:
                return HookResult(
                    success=False,
                    error=f"Unsupported translation service: {service}"
                )
                
        except Exception as e:
            return HookResult(
                success=False,
                error=f"Failed to translate: {str(e)}"
            )


class OpenAITranslationHook(Hook):
    """Hook that translates transcription text using OpenAI API."""
    
    def execute(self, context: HookContext) -> HookResult:
        """Translate the transcription text using OpenAI."""
        try:
            text = context.transcription_result.text.strip()
            target_language = self.config.get('target_language', 'Chinese')
            model = self.config.get('model', 'gpt-3.5-turbo')
            api_key = self.config.get('api_key')
            base_url = self.config.get('base_url')  # For providers like OpenRouter
            
            if not api_key:
                return HookResult(
                    success=False,
                    error="API key not configured"
                )
            
            # Import OpenAI client
            try:
                from openai import OpenAI
            except ImportError:
                return HookResult(
                    success=False,
                    error="OpenAI library not installed. Install with: pip install openai"
                )
            
            # Initialize OpenAI client with optional base_url
            client_kwargs = {'api_key': api_key}
            if base_url:
                client_kwargs['base_url'] = base_url
            
            client = OpenAI(**client_kwargs)
            
            # Create translation prompt
            system_prompt = f"You are a professional translator. Translate the following text to {target_language}. Only return the translated text, no explanations."
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=self.config.get('max_tokens', 1000),
                temperature=self.config.get('temperature', 0.3)
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Log translation
            if self.config.get('print_translation', True):
                prefix = self.config.get('output_prefix', '')
                if prefix:
                    print(f"{prefix} [{target_language}] {translated_text}")
                else:
                    print(f"[{target_language}] {translated_text}")
            
            return HookResult(
                success=True,
                message=f"Translated to {target_language} using OpenAI",
                data={
                    'original': text,
                    'translated': translated_text,
                    'target_language': target_language,
                    'model': model,
                    'usage': response.usage.model_dump() if response.usage else None
                }
            )
                
        except Exception as e:
            return HookResult(
                success=False,
                error=f"Failed to translate with OpenAI: {str(e)}"
            )
