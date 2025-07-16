"""Hook manager for post-transcription actions."""

import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from newear.utils.logging import get_logger
from .types import HookContext, HookResult


class Hook(ABC):
    """Abstract base class for hooks."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = get_logger()
    
    @abstractmethod
    def execute(self, context: HookContext) -> HookResult:
        """Execute the hook with the given context."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if the hook is enabled."""
        return self.config.get('enabled', True)


class HookManager:
    """Manager for executing hooks after transcription."""
    
    def __init__(self):
        self.hooks: List[Hook] = []
        self.logger = get_logger()
        self.session_start_time = time.time()
        self.chunk_index = 0
    
    def register_hook(self, hook: Hook):
        """Register a hook to be executed."""
        self.hooks.append(hook)
        self.logger.info(f"Registered hook: {hook.name}")
    
    def execute_hooks(self, context: HookContext) -> List[HookResult]:
        """Execute all registered hooks."""
        results = []
        
        for hook in self.hooks:
            if not hook.is_enabled():
                continue
            
            try:
                start_time = time.time()
                result = hook.execute(context)
                execution_time = time.time() - start_time
                
                if result.success:
                    self.logger.debug(f"Hook '{hook.name}' executed successfully in {execution_time:.3f}s")
                    if result.message:
                        self.logger.info(f"Hook '{hook.name}': {result.message}")
                else:
                    self.logger.warning(f"Hook '{hook.name}' failed: {result.error}")
                
                results.append(result)
                
            except Exception as e:
                error_result = HookResult(
                    success=False,
                    error=f"Hook '{hook.name}' raised exception: {str(e)}"
                )
                results.append(error_result)
                self.logger.error(f"Hook '{hook.name}' raised exception: {e}")
        
        return results
    
    def create_context(self, transcription_result, metadata: Optional[Dict[str, Any]] = None) -> HookContext:
        """Create a hook context from transcription result."""
        context = HookContext(
            transcription_result=transcription_result,
            session_start_time=self.session_start_time,
            chunk_index=self.chunk_index,
            metadata=metadata or {}
        )
        self.chunk_index += 1
        return context