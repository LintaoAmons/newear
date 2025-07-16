"""Hook factory for creating hooks from configuration."""

from typing import Dict, Any, Optional
from .manager import Hook
from .builtin import (
    ConsoleLogHook,
    FileAppendHook,
    CommandHook,
    WebhookHook,
    TranslationHook,
    OpenAITranslationHook
)


class HookFactory:
    """Factory for creating hooks from configuration."""
    
    # Map of hook types to their classes
    HOOK_TYPES = {
        'console_log': ConsoleLogHook,
        'file_append': FileAppendHook,
        'command': CommandHook,
        'webhook': WebhookHook,
        'translation': TranslationHook,
        'openai_translation': OpenAITranslationHook,
    }
    
    @classmethod
    def create_hook(cls, hook_config: Dict[str, Any]) -> Optional[Hook]:
        """Create a hook from configuration."""
        hook_type = hook_config.get('type')
        if not hook_type:
            raise ValueError("Hook configuration missing 'type' field")
        
        hook_class = cls.HOOK_TYPES.get(hook_type)
        if not hook_class:
            raise ValueError(f"Unknown hook type: {hook_type}")
        
        hook_name = hook_config.get('name', f"{hook_type}_hook")
        hook_config_data = hook_config.get('config', {})
        
        # Check if hook is enabled
        if not hook_config.get('enabled', True):
            return None
        
        return hook_class(name=hook_name, config=hook_config_data)
    
    @classmethod
    def create_hooks_from_config(cls, hooks_config: Dict[str, Any]) -> list:
        """Create hooks from complete hooks configuration."""
        hooks = []
        
        if not hooks_config.get('enabled', True):
            return hooks
        
        for hook_config in hooks_config.get('hooks', []):
            try:
                hook = cls.create_hook(hook_config)
                if hook:
                    hooks.append(hook)
            except Exception as e:
                # Log error but continue processing other hooks
                from newear.utils.logging import get_logger
                logger = get_logger()
                logger.error(f"Failed to create hook: {e}")
        
        return hooks
    
    @classmethod
    def get_available_hook_types(cls) -> list:
        """Get list of available hook types."""
        return list(cls.HOOK_TYPES.keys())