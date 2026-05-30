from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from typing import Any

from .config import AppConfig


STYLE_MAP = {
    "casual": "casual",
    "semi-formal": "semi_formal",
    "semi_formal": "semi_formal",
}


@dataclass
class ScriptTunerModel:
    model_id: str
    tokenizer: Any
    model: Any
    device: str
    is_encoder_decoder: bool


class ModelService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._lock = threading.Lock()
        self._model: ScriptTunerModel | None = None
        self._error: str | None = None
        self._loading_started = False
        self._stage = "initializing"
        self._message = "Initializing backend server"
        self._progress = 10

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "server": "ok",
                "model": {
                    "ready": self._model is not None and self._error is None,
                    "stage": self._stage,
                    "message": self._message,
                    "progress": self._progress,
                    "error": self._error,
                    "model_id": self.config.model_id,
                },
            }

    def start_loading(self) -> None:
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not token:
            self._set_status("awaiting_token", "Enter Hugging Face token", 5)
            return
        with self._lock:
            if self._loading_started:
                return
            self._loading_started = True
        thread = threading.Thread(target=self.load, name="script-tuner-loader", daemon=True)
        thread.start()

    def submit_token(self, token: str) -> dict[str, Any]:
        token = token.strip()
        if not token:
            raise ValueError("Hugging Face token is required.")
        if not token.startswith("hf_"):
            raise ValueError("Hugging Face token should start with 'hf_'.")
        os.environ["HF_TOKEN"] = token
        os.environ["HUGGINGFACE_HUB_TOKEN"] = token
        self._set_status("token_saved", "Hugging Face token saved for this session", 8)
        self.start_loading()
        return self.status()

    def _set_status(self, stage: str, message: str, progress: int) -> None:
        with self._lock:
            self._stage = stage
            self._message = message
            self._progress = progress

    def _set_error(self, error: Exception) -> None:
        with self._lock:
            self._stage = "error"
            self._message = "Model loading failed"
            self._progress = 100
            self._error = f"{type(error).__name__}: {error}"

    def load(self) -> None:
        try:
            self._set_status("loading_imports", "Loading Python inference libraries", 15)
            import torch
            from dotenv import load_dotenv
            from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer

            load_dotenv()
            token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")

            self._set_status("selecting_device", "Selecting inference device", 20)
            device = self._get_best_device(torch)
            if device == "cuda":
                dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            else:
                dtype = torch.float32

            self._set_status("loading_tokenizer", "Loading tokenizer", 30)
            tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_id,
                token=token,
                trust_remote_code=True,
            )

            self._set_status("loading_model", "Loading Script-Tuner model", 50)
            model, is_encoder_decoder = self._load_checkpoint(
                model_id=self.config.model_id,
                token=token,
                dtype=dtype,
                AutoConfig=AutoConfig,
                AutoModelForCausalLM=AutoModelForCausalLM,
                AutoModelForSeq2SeqLM=AutoModelForSeq2SeqLM,
            )

            self._set_status("moving_to_device", f"Moving model to {device}", 75)
            if device == "cpu":
                model = model.float()
            model.to(device)
            model.eval()

            if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
                tokenizer.pad_token = tokenizer.eos_token

            loaded = ScriptTunerModel(
                model_id=self.config.model_id,
                tokenizer=tokenizer,
                model=model,
                device=device,
                is_encoder_decoder=is_encoder_decoder,
            )

            with self._lock:
                self._model = loaded

            if self.config.warmup_enabled:
                self._set_status("warming_up", "Warming up inference", 90)
                self.tune("I went to the park yesterday.", "casual", warmup=True)

            self._set_status("ready", "Model ready", 100)
        except Exception as exc:
            self._set_error(exc)

    def tune(self, script: str, style: str, warmup: bool = False) -> str:
        import torch

        normalized_style = self._normalize_style(style)
        script = script.strip()
        if not script:
            raise ValueError("script is empty.")
        if len(script) > self.config.max_input_chars:
            raise ValueError(f"script is too long. Maximum length is {self.config.max_input_chars} characters.")

        with self._lock:
            tuner = self._model
            error = self._error

        if error:
            raise RuntimeError(error)
        if tuner is None:
            raise RuntimeError("Model is still loading.")

        prompt = build_opic_prompt(script, style=normalized_style)
        inputs = tuner.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_input_tokens,
        )
        inputs = {key: value.to(tuner.device) for key, value in inputs.items()}

        generation_kwargs = {
            "max_new_tokens": self.config.max_new_tokens,
            "pad_token_id": tuner.tokenizer.pad_token_id,
            "eos_token_id": tuner.tokenizer.eos_token_id,
            "repetition_penalty": self.config.repetition_penalty,
        }
        if self.config.do_sample:
            generation_kwargs.update(
                {
                    "do_sample": True,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                }
            )
        else:
            generation_kwargs.update(
                {
                    "num_beams": max(self.config.num_beams, 1),
                    "do_sample": False,
                }
            )

        with torch.inference_mode():
            output_ids = tuner.model.generate(**inputs, **generation_kwargs)

        if tuner.is_encoder_decoder:
            decoded = tuner.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        else:
            prompt_len = inputs["input_ids"].shape[-1]
            decoded = tuner.tokenizer.decode(output_ids[0][prompt_len:], skip_special_tokens=True)

        result = clean_model_output(decoded)
        if warmup:
            return result
        return result

    @staticmethod
    def _get_best_device(torch: Any) -> str:
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @staticmethod
    def _normalize_style(style: str) -> str:
        normalized = STYLE_MAP.get(style.strip().lower())
        if normalized is None:
            raise ValueError("style must be either 'casual' or 'semi-formal'.")
        return normalized

    @staticmethod
    def _load_checkpoint(
        model_id: str,
        token: str | None,
        dtype: Any,
        AutoConfig: Any,
        AutoModelForCausalLM: Any,
        AutoModelForSeq2SeqLM: Any,
    ) -> tuple[Any, bool]:
        try:
            config = AutoConfig.from_pretrained(model_id, token=token, trust_remote_code=True)
            is_encoder_decoder = bool(getattr(config, "is_encoder_decoder", True))
            model_cls = AutoModelForSeq2SeqLM if is_encoder_decoder else AutoModelForCausalLM
            model = model_cls.from_pretrained(
                model_id,
                token=token,
                torch_dtype=dtype,
                trust_remote_code=True,
            )
            return model, is_encoder_decoder
        except Exception as checkpoint_exc:
            try:
                from peft import PeftConfig, PeftModel

                peft_config = PeftConfig.from_pretrained(model_id, token=token)
                base_id = peft_config.base_model_name_or_path
                base_config = AutoConfig.from_pretrained(base_id, token=token, trust_remote_code=True)
                is_encoder_decoder = bool(getattr(base_config, "is_encoder_decoder", True))
                model_cls = AutoModelForSeq2SeqLM if is_encoder_decoder else AutoModelForCausalLM
                base_model = model_cls.from_pretrained(
                    base_id,
                    token=token,
                    torch_dtype=dtype,
                    trust_remote_code=True,
                )
                model = PeftModel.from_pretrained(base_model, model_id, token=token)
                if hasattr(model, "merge_and_unload"):
                    model = model.merge_and_unload()
                return model, is_encoder_decoder
            except Exception as adapter_exc:
                raise RuntimeError(
                    "Model loading failed. "
                    f"Full checkpoint error: {type(checkpoint_exc).__name__}: {checkpoint_exc}. "
                    f"PEFT adapter error: {type(adapter_exc).__name__}: {adapter_exc}."
                ) from adapter_exc


def build_opic_prompt(script: str, style: str = "casual") -> str:
    return (
        f"<STYLE={style}>\n"
        "Rewrite the input into natural spoken English for an OPIc speaking script. "
        "Keep the original meaning, make it sound fluent and native-like, and avoid overly formal essay style.\n\n"
        f"Input:\n{script.strip()}\n\n"
        "Output:"
    )


def clean_model_output(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^Output:\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"<STYLE=[^>]+>", "", text).strip()
    text = re.sub(r"<pause:[^>]+>", "", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text
