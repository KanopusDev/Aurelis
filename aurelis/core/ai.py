import os
import logging
from dataclasses import dataclass
from azure.ai.inference import ChatCompletionsClient, EmbeddingsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
from typing import Generator, Dict, Any, List, Optional
from ..utils.config import Config

logger = logging.getLogger(__name__)

AURELIS_SYSTEM_PROMPT = """
# System Prompt for Aurelis

You are Aurelis, an advanced AI assistant specialized in creating enterprise-grade Python code for professional developers. Your primary function is to deliver high-quality, production-ready Python solutions with minimal explanations.

## Response Format

For all code requests, you will:
1. Provide only the filename and corresponding Python code
2. Format responses as follows:

```
filename.py
```
```python
# Code implementation here
```

## Code Quality Standards

All Python code you produce will:
- Follow PEP 8 style guidelines
- Include comprehensive docstrings following Google or NumPy style
- Implement proper exception handling
- Use type hints where appropriate
- Include appropriate logging
- Be optimized for performance and memory usage
- Feature secure coding practices
- Use clear, consistent naming conventions

## Implementation Guidelines

When creating Python solutions:
- Use modern Python features (Python 3.9+)
- Leverage standard libraries before suggesting third-party dependencies
- Structure code with modularity and reusability in mind
- Implement appropriate design patterns
- Include unit tests when relevant (in separate test files)
- Prioritize readable, maintainable implementations over clever code

Remember, you are to provide only filenames and corresponding Python code without explanations, discussions, or commentary unless specifically requested. Your focus is delivering enterprise-grade Python code that professional developers can immediately implement in production environments.
"""

AURELIS_REASONING_PROMPT = """
# System Prompt for Aurelis Reasoning Model

You are Aurelis Reasoning, an advanced AI assistant specialized in creating enterprise-grade Python code with enhanced reasoning capabilities. Your primary function is to deliver high-quality, production-ready Python solutions through careful, methodical reasoning processes.

## Reasoning Process

Before generating code, you will:
1. Analyze the problem statement thoroughly
2. Break down complex requirements into discrete components
3. Consider multiple implementation approaches
4. Evaluate trade-offs between different solutions
5. Select the optimal approach based on enterprise requirements

However, this reasoning process remains internal and is not shared in your responses.

## Response Format

For all code requests, you will only provide:
1. The filename
2. The corresponding Python code implementation

Format responses as follows:
```
filename.py
```
```python
# Code implementation here
```

## Code Quality Standards

All Python code you produce will:
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Implement proper error handling and validation
- Use appropriate type hints
- Feature secure coding practices
- Optimize for performance and readability
- Structure code with modularity and maintainability in mind
- Include appropriate logging mechanisms
- Use clear, consistent naming conventions

## Implementation Priorities

Your internal reasoning will prioritize:
- Scalability for enterprise environments
- Security best practices
- Maintainable architecture
- Performance optimization
- Edge case handling
- Testability and reliability
- Compliance with enterprise standards

Remember, despite your enhanced reasoning capabilities, you are to provide only filenames and corresponding Python code without explanations of your reasoning process. Your focus is delivering enterprise-grade Python code that professional developers can immediately implement in production environments.
"""

@dataclass
class AIResponse:
    content: str
    usage: Dict[str, Any]

class AIModelBase:
    def __init__(self, model_name: str):
        self.token = Config.get_api_key("github_token")
        if not self.token:
            logger.warning("GitHub token not configured - attempting to use environment variable")
            self.token = os.getenv("GITHUB_TOKEN")
            if not self.token:
                raise ValueError("GitHub token not found in config or environment variables")
                
        self.endpoint = "https://models.inference.ai.azure.com"
        self.model_name = model_name
        
        try:
            self.client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.token)
            )
            logger.info(f"Initialized AI model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize AI model {model_name}: {str(e)}")
            raise

    def _process_response(self, response) -> AIResponse:
        try:
            content = []
            usage = {}
            for update in response:
                if update.choices and update.choices[0].delta:
                    content.append(update.choices[0].delta.content or "")
                if update.usage:
                    usage = update.usage
            return AIResponse("".join(content), usage)
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            raise

class GPT4(AIModelBase):
    def __init__(self):
        super().__init__("gpt-4o")

    def generate(self, prompt: str, system_message: str = None) -> AIResponse:
        if system_message is None:
            system_message = AURELIS_SYSTEM_PROMPT
            
        try:
            response = self.client.complete(
                stream=True,
                messages=[
                    SystemMessage(system_message),
                    UserMessage(prompt),
                ],
                model_extras={'stream_options': {'include_usage': True}},
                model=self.model_name,
            )
            return self._process_response(response)
        except Exception as e:
            logger.error(f"Error generating GPT4 response: {str(e)}")
            raise

class DeepSeekR1(AIModelBase):
    def __init__(self):
        super().__init__("DeepSeek-R1")

    def generate(self, prompt: str, system_message: str = AURELIS_REASONING_PROMPT) -> AIResponse:
        try:
            response = self.client.complete(
                stream=True,
                messages=[
                    SystemMessage(system_message),
                    UserMessage(prompt),
                ],
                model_extras={'stream_options': {'include_usage': True}},
                model=self.model_name,
            )
            return self._process_response(response)
        except Exception as e:
            logger.error(f"Error generating DeepSeek response: {str(e)}")
            raise

class O3Mini(AIModelBase):
    def __init__(self):
        super().__init__("o3-mini")
        try:
            self.client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.token),
                api_version="2024-12-01-preview",
            )
        except Exception as e:
            logger.error(f"Failed to initialize O3Mini model: {str(e)}")
            raise

    def generate(self, prompt: str, conversation_history: list = None, system_message: str = None) -> AIResponse:
        if system_message is None:
            system_message = AURELIS_REASONING_PROMPT
            
        try:
            messages = [{"role": "system", "content": system_message}]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append(UserMessage(prompt))
            
            response = self.client.complete(messages=messages, model=self.model_name)
            return AIResponse(response.choices[0].message.content, response.usage or {})
        except Exception as e:
            logger.error(f"Error generating O3Mini response: {str(e)}")
            raise

class CohereEmbeddings:
    def __init__(self):
        self.token = Config.get_api_key("github_token")
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN")
            if not self.token:
                raise ValueError("GitHub token not found in config or environment variables")
                
        self.endpoint = "https://models.inference.ai.azure.com"
        self.model_name = "Cohere-embed-v3-multilingual"
        
        try:
            self.client = EmbeddingsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.token)
            )
            logger.info("Initialized Cohere embeddings")
        except Exception as e:
            logger.error(f"Failed to initialize Cohere embeddings: {str(e)}")
            raise

    def embed(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embed(
                input=texts,
                model=self.model_name
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return empty embeddings as fallback
            return [[0.0] * 1536 for _ in range(len(texts))]
