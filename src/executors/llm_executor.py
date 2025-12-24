from __future__ import annotations

import os
import logging
import json
from typing import Any, Dict, List, Optional
from openai import OpenAI

from src.core.executor import BaseExecutor

logger = logging.getLogger(__name__)

class LLMExecutor(BaseExecutor):
    """
    Executor for Large Language Model (LLM) tasks.
    Handles document classification and field extraction specific to Indian documents.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM executor.
        
        Args:
            config: Configuration dictionary. 
                    Uses OPENAI_API_KEY from environment if not provided in config.
        """
        super().__init__(config)
        api_key = self.config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in config or environment")
        
        self.client = OpenAI(api_key=api_key)

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LLM tasks based on task_type.

        Args:
            inputs: Dictionary containing:
                - task_type: 'classify', 'extract', or 'completion'
                - text: Text content (required for classify/extract)
                - document_type: Type of document (required for extract)
                - ... other args for completion

        Returns:
            Dictionary containing the task result.
        """
        task_type = inputs.get("task_type")
        
        if task_type == "classify":
            text = inputs.get("text")
            if not text:
                raise ValueError("Text is required for classification")
            return self.classify_document(text)
            
        elif task_type == "extract":
            text = inputs.get("text")
            document_type = inputs.get("document_type")
            if not text:
                raise ValueError("Text is required for extraction")
            if not document_type:
                raise ValueError("Document type is required for extraction")
            return self.extract_fields(text, document_type)
            
        elif task_type == "completion":
            messages = inputs.get("messages")
            if not messages:
                prompt = inputs.get("prompt")
                if not prompt:
                     raise ValueError("Either 'messages' or 'prompt' is required for completion")
                messages = [{"role": "user", "content": prompt}]
            
            model = inputs.get("model", "gpt-4o-mini")
            return self.completion(messages, model)
            
        else:
            raise ValueError(f"Unknown task_type: {task_type}")

    def completion(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """
        Perform a generic chat completion.
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages
        )
        content = response.choices[0].message.content
        return {"content": content}

    def classify_document(self, text: str) -> Dict[str, Any]:
        """
        Classify the document text into predefined categories.
        
        Categories: aadhaar, pan, passport, driving_license, other
        """
        system_prompt = (
            "You are a document classifier for Indian identity documents. "
            "Classify the input text into one of the following categories: "
            "aadhaar, pan, passport, driving_license, other. "
            "Return JSON with keys: document_type, confidence (0-1), reasoning."
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:4000]} # Truncate if too long to save tokens
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Received empty response from LLM")
            
        return json.loads(content)

    def extract_fields(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Extract structured fields from the document text based on its type.
        """
        if document_type == "aadhaar":
            return self._extract_aadhaar(text)
        elif document_type == "pan":
            return self._extract_pan(text)
        else:
             raise ValueError(f"Unsupported document type for extraction: {document_type}")

    def _extract_aadhaar(self, text: str) -> Dict[str, Any]:
        system_prompt = (
            "Extract the following fields from the Aadhaar card text: "
            "name, aadhaar_number, dob (YYYY-MM-DD), gender, address, confidence (0-1). "
            "Return JSON object."
        )
        return self._call_llm_extraction(system_prompt, text)

    def _extract_pan(self, text: str) -> Dict[str, Any]:
        system_prompt = (
            "Extract the following fields from the PAN card text: "
            "name, pan_number, father_name, dob (YYYY-MM-DD), confidence (0-1). "
            "Return JSON object."
        )
        return self._call_llm_extraction(system_prompt, text)

    def _call_llm_extraction(self, system_prompt: str, text: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:4000]}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Received empty response from LLM")
            
        return json.loads(content)
