"""
Custom workflows package.

Import this package to register example workflows with the WorkflowRegistry.

Example:
    from inference import WorkflowRegistry
    import inference.workflows  # This registers the example workflows
    
    # Now you can use them
    print(WorkflowRegistry.list_workflows())  # ['code_focused', 'quick_only', 'force_complex']
"""

# Import examples to register them
from . import examples

__all__ = ["examples"]
