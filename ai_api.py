"""Azure OpenAI API helper utilities.

This module provides:
  * AI client initialization with Azure AD authentication
  * GPT model interaction functions
  * Environment variable configuration support
"""

import os
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


class AzureAIClient:
    """Azure OpenAI client with proper authentication and configuration."""
    
    def __init__(self):
        # Load environment variables from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # dotenv not installed, rely on system env vars
        
        # Configuration from environment variables (no hardcoded defaults)
        self.endpoint = self._get_required_env("AZURE_OPENAI_ENDPOINT")
        self.model_name = self._get_required_env("AZURE_OPENAI_MODEL")
        self.deployment = self._get_required_env("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = self._get_required_env("AZURE_OPENAI_API_VERSION")
        
        # Token limits from environment variables
        self.default_max_tokens = int(os.getenv("AZURE_OPENAI_MAX_TOKENS_DEFAULT", "2000"))
        self.max_retry_tokens = int(os.getenv("AZURE_OPENAI_MAX_RETRY_TOKENS", "8000"))
        
        self._client = None
        
        # Validate configuration on initialization
        self._validate_config()
        
    def _get_required_env(self, var_name: str) -> str:
        """Get a required environment variable or raise an error."""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(
                f"Required environment variable '{var_name}' is not set. "
                f"Please configure it in your .env file or environment."
            )
        return value.strip()
    
    def _validate_config(self):
        """Validate the Azure OpenAI configuration."""
        # Validate endpoint format
        if not self.endpoint.startswith("https://"):
            raise ValueError(f"AZURE_OPENAI_ENDPOINT must start with 'https://': {self.endpoint}")
        
        if not self.endpoint.endswith("/"):
            self.endpoint += "/"
        
        # Validate API version format
        if not self.api_version.startswith("20"):
            raise ValueError(f"AZURE_OPENAI_API_VERSION should be in format YYYY-MM-DD: {self.api_version}")
        
        # Validate model and deployment are not empty
        if not self.model_name or not self.deployment:
            raise ValueError("AZURE_OPENAI_MODEL and AZURE_OPENAI_DEPLOYMENT cannot be empty")
        
        print(f"✅ Azure OpenAI Configuration Loaded:")
        print(f"   🌐 Endpoint: {self.endpoint}")
        print(f"   🤖 Model: {self.model_name}")
        print(f"   🚀 Deployment: {self.deployment}")
        print(f"   📅 API Version: {self.api_version}")
        print(f"   🎯 Default Max Tokens: {self.default_max_tokens}")
        print(f"   🔄 Max Retry Tokens: {self.max_retry_tokens}")
        
    def _get_client(self) -> AzureOpenAI:
        """Initialize and cache the Azure OpenAI client."""
        if self._client is None:
            try:
                # Set up authentication with Azure AD
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(), 
                    "https://cognitiveservices.azure.com/.default"
                )
                
                # Initialize client
                self._client = AzureOpenAI(
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint,
                    azure_ad_token_provider=token_provider,
                )
                
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Azure OpenAI client: {e}") from e
                
        return self._client
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = None,
        auto_retry: bool = True
    ) -> str:
        """
        Get a chat completion from the Azure OpenAI model.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in the response
            auto_retry: Automatically retry with more tokens if response is truncated
            
        Returns:
            The generated response content as a string
        """
        
        # Get default from environment or use configured default
        if max_tokens is None:
            max_tokens = self.default_max_tokens
        
        def _attempt_completion(attempt_max_tokens: int, attempt_number: int = 1) -> Dict[str, Any]:
            """Internal method to attempt completion with token monitoring."""
            try:
                client = self._get_client()
                
                # For GPT-5-mini, ensure minimum token limit to account for reasoning tokens
                min_tokens = int(os.getenv("AZURE_OPENAI_MIN_TOKENS_GPT5", "500"))
                if self.model_name == "gpt-5-mini" and attempt_max_tokens < min_tokens:
                    attempt_max_tokens = min_tokens
                
                # Prepare request parameters - following Azure sample code pattern
                request_params = {
                    "messages": messages,
                    "max_completion_tokens": attempt_max_tokens,
                    "model": self.deployment
                }
                
                response = client.chat.completions.create(**request_params)
                
                # Get response details
                content = response.choices[0].message.content or ""
                finish_reason = response.choices[0].finish_reason
                usage = response.usage
                
                # Check for truncation warning
                is_truncated = finish_reason == "length"
                
                # Calculate token efficiency
                reasoning_tokens = 0
                if hasattr(usage.completion_tokens_details, 'reasoning_tokens'):
                    reasoning_tokens = usage.completion_tokens_details.reasoning_tokens
                
                content_tokens = usage.completion_tokens - reasoning_tokens
                
                # Provide detailed feedback
                if attempt_number == 1:  # Only log on first attempt to avoid spam
                    print(f"🤖 AI Response (Attempt {attempt_number}):")
                    print(f"   📝 Content length: {len(content)} characters")
                    print(f"   💰 Token usage: {usage.completion_tokens}/{attempt_max_tokens}")
                    if reasoning_tokens > 0:
                        print(f"   🧠 Reasoning tokens: {reasoning_tokens}")
                        print(f"   📄 Content tokens: {content_tokens}")
                    
                    if is_truncated:
                        print(f"   ⚠️  Response truncated - consider increasing max_tokens")
                    else:
                        print(f"   ✅ Complete response")
                
                return {
                    "content": content,
                    "is_truncated": is_truncated,
                    "finish_reason": finish_reason,
                    "tokens_used": usage.completion_tokens,
                    "tokens_limit": attempt_max_tokens,
                    "reasoning_tokens": reasoning_tokens,
                    "content_tokens": content_tokens
                }
                
            except Exception as e:
                return {"error": str(e)}
        
        # First attempt
        result = _attempt_completion(max_tokens, 1)
        
        if "error" in result:
            raise RuntimeError(f"Failed to get chat completion: {result['error']}")
        
        # Auto-retry logic if enabled and response was truncated
        if auto_retry and result["is_truncated"] and max_tokens < self.max_retry_tokens:
            print(f"🔄 Auto-retrying with increased token limit...")
            
            # Increase tokens intelligently based on current usage
            tokens_used = result["tokens_used"]
            
            # Get retry multiplier from environment
            retry_multiplier = float(os.getenv("AZURE_OPENAI_RETRY_MULTIPLIER", "1.5"))
            estimated_needed = int(tokens_used * retry_multiplier)
            new_max_tokens = min(estimated_needed, self.max_retry_tokens)
            
            if new_max_tokens > max_tokens:
                print(f"   📈 Increasing from {max_tokens} to {new_max_tokens} tokens")
                retry_result = _attempt_completion(new_max_tokens, 2)
                
                if "error" not in retry_result and not retry_result["is_truncated"]:
                    print(f"   ✅ Retry successful - complete response received")
                    return retry_result["content"]
                else:
                    print(f"   ⚠️  Retry still truncated or failed")
            
        return result["content"]

    def estimate_tokens_needed(self, data_size: str, analysis_type: str = "summary") -> int:
        """
        Estimate optimal max_completion_tokens based on data size and analysis type.
        
        Args:
            data_size: "small" (1-5 items), "medium" (5-20 items), "large" (20+ items)
            analysis_type: "summary", "detailed", "comprehensive"
        
        Returns:
            Recommended max_completion_tokens value
        """
        # Base recommendations matrix - configurable via environment
        default_recommendations = {
            "summary": {"small": 1000, "medium": 1500, "large": 2500},
            "detailed": {"small": 2000, "medium": 3000, "large": 4500}, 
            "comprehensive": {"small": 3000, "medium": 4500, "large": 6000}
        }
        
        # Allow override via environment variables
        env_key = f"AZURE_OPENAI_TOKENS_{analysis_type.upper()}_{data_size.upper()}"
        env_value = os.getenv(env_key)
        
        if env_value:
            base_tokens = int(env_value)
        else:
            base_tokens = default_recommendations.get(analysis_type, default_recommendations["summary"]).get(data_size, 2000)
        
        # Adjust for GPT-5-mini reasoning tokens
        min_tokens = int(os.getenv("AZURE_OPENAI_MIN_TOKENS_GPT5", "500"))
        if self.model_name == "gpt-5-mini":
            base_tokens = max(base_tokens, min_tokens)
        
        # Cap at model limits
        max_allowed = min(base_tokens, self.max_retry_tokens)
        
        print(f"💡 Token Recommendation:")
        print(f"   📊 Data size: {data_size}, Analysis: {analysis_type}")
        print(f"   🎯 Recommended tokens: {max_allowed}")
        print(f"   📈 Auto-retry enabled up to {self.max_retry_tokens} tokens if truncated")
        
        return max_allowed

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Azure OpenAI and return diagnostic info.
        
        Returns:
            Dict with test results and model information
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": "Hello! Please confirm you're working and tell me what model you are."
                }
            ]
            
            client = self._get_client()
            
            # Use configurable test tokens
            test_tokens = int(os.getenv("AZURE_OPENAI_TEST_TOKENS", "500"))
            
            request_params = {
                "messages": messages,
                "max_completion_tokens": test_tokens,
                "model": self.deployment
            }
            
            response = client.chat.completions.create(**request_params)
            
            result = {
                "success": True,
                "response": response.choices[0].message.content,
                "endpoint": self.endpoint,
                "model": self.model_name,
                "deployment": self.deployment,
                "api_version": self.api_version
            }
            
            # Add usage info if available
            if hasattr(response, 'usage'):
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "endpoint": self.endpoint,
                "model": self.model_name,
                "deployment": self.deployment,
                "api_version": self.api_version
            }


# Global instance
_ai_client: Optional[AzureAIClient] = None


def get_ai_client() -> AzureAIClient:
    """Get the global AI client instance (singleton pattern)."""
    global _ai_client
    if _ai_client is None:
        _ai_client = AzureAIClient()
    return _ai_client


def chat_with_ai(
    messages: List[Dict[str, str]], 
    max_tokens: int = None,  # Remove hardcoded default
    temperature: Optional[float] = None
) -> str:
    """
    Convenience function for getting AI chat completions.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_tokens: Maximum tokens in the response (uses environment default if None)
        temperature: Sampling temperature (None for default)
        
    Returns:
        The generated response content as a string
    """
    client = get_ai_client()
    
    # Smart token allocation based on message count if not specified
    if max_tokens is None:
        if len(messages) <= 5:
            max_tokens = client.estimate_tokens_needed("small", "detailed")  # 2000
        elif len(messages) <= 20:
            max_tokens = client.estimate_tokens_needed("medium", "summary")  # 1500  
        else:
            max_tokens = client.estimate_tokens_needed("large", "comprehensive")  # 6000

    # Auto-retry enabled by default
    response = client.chat_completion(messages, max_tokens=max_tokens, auto_retry=True)
    
    return response


def test_ai_connection() -> Dict[str, Any]:
    """Test the AI connection and return diagnostic info."""
    client = get_ai_client()
    return client.test_connection()


__all__ = [
    "AzureAIClient",
    "get_ai_client", 
    "chat_with_ai",
    "test_ai_connection"
]
