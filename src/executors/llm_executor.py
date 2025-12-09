# src/executors/llm_executor.py
import os
from typing import Dict, Any
from .base import BaseExecutor

class LLMExecutor(BaseExecutor):
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> str:
        """
        Call LLM with prompt
        
        config:
            model: "gpt-4" or "ollama/llama2"
            prompt: "You are a helpful assistant..."
            max_tokens: 2000
        
        inputs:
            query: user query
            context: additional context
        """
        model = config.get("model", "gpt-4")
        prompt_template = config.get("prompt", "")
        max_tokens = config.get("max_tokens", 2000)
        
        # Format prompt with inputs
        import os
        from typing import Dict, Any, Optional
        from .base import BaseExecutor

        import requests


        class LLMExecutor(BaseExecutor):
            """Executor that calls local Ollama or OpenAI backends.

            This implementation is defensive: it supports the new `openai.OpenAI` client
            if available, and falls back to the older `openai` module shape when needed.
            Ollama calls are sent to a local HTTP endpoint and parsed with fallbacks.
            """

            def __init__(self, openai_api_key: Optional[str] = None):
                # Allow injecting the API key for tests; otherwise read from env
                self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

            def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> str:
                """Build prompt from template and route to the correct model backend."""
                model = config.get("model", "gpt-4")
                prompt_template = config.get("prompt", "")
                max_tokens = config.get("max_tokens", 2000)

                # Safely format prompt (if keys are missing, KeyError will surface clearly)
                prompt = prompt_template.format(**(inputs or {}))

                if isinstance(model, str) and model.startswith("ollama/"):
                    return self._call_ollama(model, prompt, max_tokens)
                return self._call_openai(model, prompt, max_tokens)

            def _call_openai(self, model: str, prompt: str, max_tokens: int) -> str:
                """Call OpenAI-compatible API. Tries new and legacy clients."""
                # Try new OpenAI client first (openai.OpenAI)
                try:
                    try:
                        from openai import OpenAI

                        client = OpenAI(api_key=self.openai_api_key)
                        resp = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=max_tokens,
                        )
                        # new client: resp.choices[0].message.content
                        choice = resp.choices[0]
                        # If the choice is dict-like, prefer safe dict access
                        if isinstance(choice, dict):
                            return choice.get("message", {}).get("content", "")
                        # Otherwise try attribute access on message
                        msg = getattr(choice, "message", None)
                        if msg is not None:
                            if isinstance(msg, dict):
                                return msg.get("content", "")
                            return getattr(msg, "content", "")
                        # As a last resort, stringify
                        return str(choice)
                    except Exception:
                        # Fallback to legacy openai package shape
                        import openai

                        openai.api_key = self.openai_api_key
                        # Some openai package versions expose ChatCompletion, some do not.
                        chat_cls = getattr(openai, "ChatCompletion", None)
                        if chat_cls is not None and hasattr(chat_cls, "create"):
                            resp = chat_cls.create(
                                model=model,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=max_tokens,
                            )
                        else:
                            # Fall back to the older Completion API which uses prompt instead.
                            # Use getattr to avoid static-analysis errors when the attribute
                            # is not present in the installed openai stub.
                            comp_cls = getattr(openai, "Completion", None)
                            if comp_cls is not None and hasattr(comp_cls, "create"):
                                resp = comp_cls.create(
                                    model=model,
                                    prompt=prompt,
                                    max_tokens=max_tokens,
                                )
                            else:
                                raise RuntimeError("OpenAI client does not expose a compatible Completion API")

                        # Attempt to extract text from the legacy response
                        choice = resp.choices[0]
                        if isinstance(choice, dict):
                            return choice.get("message", {}).get("content", "") or choice.get("text", "")
                        # attribute based
                        msg = getattr(choice, "message", None)
                        if msg is not None:
                            return getattr(msg, "content", "")
                        return getattr(choice, "text", "") or str(choice)
                except Exception as e:
                    raise RuntimeError(f"OpenAI API error: {e}")

            def _call_ollama(self, model: str, prompt: str, max_tokens: int) -> str:
                """Call local Ollama model via HTTP API.

                Returns the text response or raises RuntimeError on failure.
                """
                model_name = model.split("/", 1)[-1]
                url = "http://localhost:11434/api/generate"
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    # include max_tokens for compatibility if supported by Ollama
                    "max_tokens": max_tokens,
                    "stream": False,
                }

                try:
                    resp = requests.post(url, json=payload, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    # Ollama responses vary; try common keys
                    for key in ("response", "output", "text", "result"):
                        if key in data:
                            return data[key]
                    # Some Ollama endpoints return a list or nested structure
                    # Try to pull a sensible fallback
                    if isinstance(data, dict) and "choices" in data:
                        first = data["choices"][0]
                        if isinstance(first, dict):
                            return first.get("text") or first.get("message") or str(first)
                    # As a last resort, return the full JSON as a string
                    return str(data)
                except Exception as e:
                    raise RuntimeError(f"Ollama error: {e}")

