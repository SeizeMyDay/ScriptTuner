from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    model_id: str = os.getenv(
        "SCRIPT_TUNER_MODEL_ID",
        "aip-scripttuner-team/scripttuner-t5gemma2-1b-combined",
    )
    host: str = os.getenv("SCRIPT_TUNER_HOST", "127.0.0.1")
    port: int = int(os.getenv("SCRIPT_TUNER_PORT", "7860"))
    max_input_chars: int = int(os.getenv("SCRIPT_TUNER_MAX_INPUT_CHARS", "4000"))
    max_input_tokens: int = int(os.getenv("SCRIPT_TUNER_MAX_INPUT_TOKENS", "1024"))
    max_new_tokens: int = int(os.getenv("SCRIPT_TUNER_MAX_NEW_TOKENS", "256"))
    num_beams: int = int(os.getenv("SCRIPT_TUNER_NUM_BEAMS", "1"))
    do_sample: bool = os.getenv("SCRIPT_TUNER_DO_SAMPLE", "0") == "1"
    temperature: float = float(os.getenv("SCRIPT_TUNER_TEMPERATURE", "0.7"))
    top_p: float = float(os.getenv("SCRIPT_TUNER_TOP_P", "0.9"))
    repetition_penalty: float = float(os.getenv("SCRIPT_TUNER_REPETITION_PENALTY", "1.0"))
    request_timeout_seconds: int = int(os.getenv("SCRIPT_TUNER_REQUEST_TIMEOUT_SECONDS", "120"))
    warmup_enabled: bool = os.getenv("SCRIPT_TUNER_WARMUP", "1") != "0"
