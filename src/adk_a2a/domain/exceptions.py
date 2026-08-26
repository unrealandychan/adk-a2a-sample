"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base exception for all domain-related errors."""


class AgentExecutionError(DomainError):
    """Raised when an agent fails to execute a assigned goal or instruction."""


class ToolExecutionError(DomainError):
    """Raised when an agent tool fails during execution."""


class A2ACommunicationError(DomainError):
    """Raised when an A2A remote agent invocation fails."""
