"""Dynamic workflow registration and management."""

from typing import Dict, Callable, Any, Optional, List


class WorkflowRegistry:
    """
    Registry for custom classification workflows.
    
    Allows registering custom workflow functions that can be invoked by name.
    This enables easy extension and modification of classification behavior.
    """
    
    _workflows: Dict[str, Callable] = {}
    _metadata: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(
        cls, 
        name: str, 
        description: str = "",
        author: str = "",
        version: str = "1.0.0"
    ) -> Callable:
        """
        Decorator to register a workflow function.
        
        Args:
            name: Unique workflow name.
            description: Human-readable description.
            author: Optional author identifier.
            version: Workflow version.
            
        Returns:
            Decorator function.
            
        Example:
            @WorkflowRegistry.register("my_workflow", description="Custom workflow")
            def my_workflow(prompt: str, config: dict) -> dict:
                # Custom processing logic
                return {"result": "..."}
        """
        def decorator(func: Callable) -> Callable:
            cls._workflows[name] = func
            cls._metadata[name] = {
                "description": description,
                "author": author,
                "version": version,
                "function": func.__name__,
            }
            return func
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Callable:
        """
        Get a registered workflow by name.
        
        Args:
            name: Workflow name.
            
        Returns:
            Workflow function.
            
        Raises:
            KeyError: If workflow not found.
        """
        if name not in cls._workflows:
            available = ", ".join(cls._workflows.keys()) or "none"
            raise KeyError(
                f"Workflow '{name}' not found. Available workflows: {available}"
            )
        return cls._workflows[name]
    
    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a workflow is registered."""
        return name in cls._workflows
    
    @classmethod
    def list_workflows(cls) -> List[str]:
        """List all registered workflow names."""
        return list(cls._workflows.keys())
    
    @classmethod
    def get_metadata(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a workflow.
        
        Args:
            name: Workflow name.
            
        Returns:
            Metadata dictionary or None if not found.
        """
        return cls._metadata.get(name)
    
    @classmethod
    def list_all(cls) -> Dict[str, Dict[str, Any]]:
        """
        List all workflows with their metadata.
        
        Returns:
            Dictionary mapping workflow names to metadata.
        """
        return dict(cls._metadata)
    
    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Remove a workflow from the registry.
        
        Args:
            name: Workflow name to remove.
            
        Returns:
            True if removed, False if not found.
        """
        if name in cls._workflows:
            del cls._workflows[name]
            del cls._metadata[name]
            return True
        return False
    
    @classmethod
    def clear(cls) -> None:
        """Remove all registered workflows."""
        cls._workflows.clear()
        cls._metadata.clear()
