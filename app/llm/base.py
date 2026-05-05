class BaseLLMProvider:
    """Abstract base class for all LLM providers."""
    
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> str:
        """Generate a response given a system and user prompt."""
        raise NotImplementedError
        
    def name(self) -> str:
        """Return the lowercase name of the provider."""
        raise NotImplementedError
