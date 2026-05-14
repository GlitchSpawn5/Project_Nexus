class LLMProviderError(Exception):
    """Raised when an LLM provider fails to generate a completion."""
    def __init__(self, provider_name: str, original_error: str):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"[{provider_name}] failed: {original_error}")
