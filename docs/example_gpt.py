#!/usr/bin/env python3
"""
chatgpt_pipeline.py

A finer-granularity ChatGPT invocation pipeline with three major modules:

1) Pre-processing module
2) Inference module
3) Post-processing module

Refined workflow:

user
-> user request
-> pre-processing module
-> model input
-> inference module
-> model output
-> post-processing module
-> final response
-> user

Setup:
    pip install openai

Environment:
    export OPENAI_API_KEY="your_api_key_here"

Run:
    python chatgpt_pipeline.py
"""

from __future__ import annotations
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, Any
from openai import OpenAI


# ============================================================
# Shared data models
# ============================================================

@dataclass
class UserRequest:
    text: str


@dataclass
class PreprocessResult:
    raw_user_input: str
    validated_input: str
    normalized_input: str
    system_instruction: str
    packaged_model_input: str
    metadata: Dict[str, Any]


@dataclass
class InferenceResult:
    raw_response_object: Any
    request_payload: Dict[str, Any]
    raw_text: str
    metadata: Dict[str, Any]


@dataclass
class PostprocessResult:
    final_text: str
    metadata: Dict[str, Any]


# ============================================================
# 1) PRE-PROCESSING MODULE
# ============================================================
#
# Conceptual imports for this module:
#   import re
#   from dataclasses import dataclass
#   from typing import Dict, Any
#
# Sub-modules:
#   1.1 InputValidationSubmodule
#   1.2 NormalizationSubmodule
#   1.3 ContextAssemblySubmodule
#   1.4 RequestPackagingSubmodule
# ============================================================

class InputValidationSubmodule:
    def run(self, user_input: str) -> str:
        if not user_input or not user_input.strip():
            raise ValueError("User input must not be empty.")
        return user_input


class NormalizationSubmodule:
    @staticmethod
    def run(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text


class ContextAssemblySubmodule:
    def run(self, normalized_input: str) -> tuple[str, Dict[str, Any]]:
        system_instruction = (
            "You are ChatGPT, a precise and helpful assistant. "
            "Answer clearly, directly, and with practical detail."
        )

        metadata = {
            "language_hint": self._guess_language(normalized_input),
            "normalized_length": len(normalized_input),
        }
        return system_instruction, metadata

    @staticmethod
    def _guess_language(text: str) -> str:
        if re.search(r"[\u4e00-\u9fff]", text):
            return "zh"
        return "en"


class RequestPackagingSubmodule:
    def run(self, normalized_input: str, system_instruction: str) -> str:
        # In this simplified design, packaged_model_input is just the cleaned text.
        # In a richer design, this could be a structured message list.
        _ = system_instruction
        return normalized_input


class PreProcessingModule:
    def __init__(self) -> None:
        self.validator = InputValidationSubmodule()
        self.normalizer = NormalizationSubmodule()
        self.context_assembler = ContextAssemblySubmodule()
        self.request_packager = RequestPackagingSubmodule()

    def run(self, user_input: str) -> PreprocessResult:
        validated_input = self.validator.run(user_input)
        normalized_input = self.normalizer.run(validated_input)
        system_instruction, context_metadata = self.context_assembler.run(normalized_input)
        packaged_model_input = self.request_packager.run(normalized_input, system_instruction)

        metadata = {
            "raw_length": len(user_input),
            "validated_length": len(validated_input),
            **context_metadata,
        }

        return PreprocessResult(
            raw_user_input=user_input,
            validated_input=validated_input,
            normalized_input=normalized_input,
            system_instruction=system_instruction,
            packaged_model_input=packaged_model_input,
            metadata=metadata,
        )


# ============================================================
# 2) INFERENCE MODULE
# ============================================================
#
# Conceptual imports for this module:
#   import os
#   from typing import Any, Dict
#   from openai import OpenAI
#
# Sub-modules:
#   2.1 ClientInitializationSubmodule
#   2.2 RequestConstructionSubmodule
#   2.3 ResponseInvocationSubmodule
#   2.4 ResponseExtractionSubmodule
# ============================================================

class ClientInitializationSubmodule:
    def run(self) -> OpenAI:
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError(
                "OPENAI_API_KEY is not set. Please export your API key first."
            )
        return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class RequestConstructionSubmodule:
    def __init__(self, model: str) -> None:
        self.model = model

    def run(self, preprocessed: PreprocessResult) -> Dict[str, Any]:
        return {
            "model": self.model,
            "instructions": preprocessed.system_instruction,
            "input": preprocessed.packaged_model_input,
        }


class ResponseInvocationSubmodule:
    def run(self, client: OpenAI, payload: Dict[str, Any]) -> Any:
        return client.responses.create(**payload)


class ResponseExtractionSubmodule:
    def run(self, response: Any) -> tuple[str, Dict[str, Any]]:
        raw_text = getattr(response, "output_text", "")
        metadata = {
            "empty_model_output": not bool(raw_text.strip()),
        }
        return raw_text, metadata


class InferenceModule:
    def __init__(self, model: str = "gpt-5.4") -> None:
        self.client_initializer = ClientInitializationSubmodule()
        self.request_constructor = RequestConstructionSubmodule(model=model)
        self.response_invoker = ResponseInvocationSubmodule()
        self.response_extractor = ResponseExtractionSubmodule()
        self.client = self.client_initializer.run()

    def run(self, preprocessed: PreprocessResult) -> InferenceResult:
        payload = self.request_constructor.run(preprocessed)
        response = self.response_invoker.run(self.client, payload)
        raw_text, metadata = self.response_extractor.run(response)

        return InferenceResult(
            raw_response_object=response,
            request_payload=payload,
            raw_text=raw_text,
            metadata=metadata,
        )


# ============================================================
# 3) POST-PROCESSING MODULE
# ============================================================
#
# Conceptual imports for this module:
#   from dataclasses import dataclass
#   from typing import Dict, Any
#
# Sub-modules:
#   3.1 OutputCleaningSubmodule
#   3.2 OutputValidationSubmodule
#   3.3 OutputRenderingSubmodule
#   3.4 OutputMetadataSubmodule
# ============================================================

class OutputCleaningSubmodule:
    @staticmethod
    def run(text: str) -> str:
        text = text.strip()
        if not text:
            return "[No text returned by model]"
        return text


class OutputValidationSubmodule:
    @staticmethod
    def run(text: str) -> str:
        # Placeholder for policy checks, redaction, or schema validation.
        return text


class OutputRenderingSubmodule:
    @staticmethod
    def run(text: str) -> str:
        # Placeholder for markdown rendering, JSON formatting, etc.
        return text


class OutputMetadataSubmodule:
    @staticmethod
    def run(preprocessed: PreprocessResult, final_text: str) -> Dict[str, Any]:
        return {
            "input_language_hint": preprocessed.metadata.get("language_hint"),
            "output_length": len(final_text),
            "empty_output": not bool(final_text.strip()),
        }


class PostProcessingModule:
    def __init__(self) -> None:
        self.cleaner = OutputCleaningSubmodule()
        self.validator = OutputValidationSubmodule()
        self.renderer = OutputRenderingSubmodule()
        self.metadata_builder = OutputMetadataSubmodule()

    def run(
        self,
        preprocessed: PreprocessResult,
        inferred: InferenceResult,
    ) -> PostprocessResult:
        cleaned = self.cleaner.run(inferred.raw_text)
        validated = self.validator.run(cleaned)
        rendered = self.renderer.run(validated)
        metadata = self.metadata_builder.run(preprocessed, rendered)

        return PostprocessResult(
            final_text=rendered,
            metadata=metadata,
        )


# ============================================================
# PIPELINE ORCHESTRATION LAYER
# ============================================================
#
# Conceptual imports for this layer:
#   import sys
#   from __future__ import annotations
#
# Role:
#   Composes the three major modules into one intact workflow.
# ============================================================

class ChatGPTPipeline:
    def __init__(self, model: str = "gpt-5.4") -> None:
        self.pre_processor = PreProcessingModule()
        self.inference = InferenceModule(model=model)
        self.post_processor = PostProcessingModule()

    def run(self, user_input: str) -> PostprocessResult:
        preprocessed = self.pre_processor.run(user_input)
        inferred = self.inference.run(preprocessed)
        postprocessed = self.post_processor.run(preprocessed, inferred)
        return postprocessed


def main() -> int:
    try:
        if len(sys.argv) > 1:
            user_input = " ".join(sys.argv[1:])
        else:
            user_input = input("Enter your prompt: ")

        pipeline = ChatGPTPipeline(model="gpt-5.4")
        result = pipeline.run(user_input)

        print("\n=== Final Output ===")
        print(result.final_text)

        print("\n=== Post-processing Metadata ===")
        for k, v in result.metadata.items():
            print(f"{k}: {v}")

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())