# Script-Tuner Local Service

Double-click `ScriptTuner.hta` on Windows. It starts the local backend and opens
the web UI automatically.

If HTA execution is blocked by Windows policy, double-click
`Start ScriptTuner.bat` instead, then use the browser tab that opens.

On first run, the launcher creates `.venv` and installs packages from
`requirements.txt`. The user only needs Python 3.11 or newer installed.

The local service exposes:

- `GET /health`
- `GET /status`
- `POST /token`
- `POST /tune`

Environment variables:

- `SCRIPT_TUNER_MODEL_ID`
- `SCRIPT_TUNER_HOST`
- `SCRIPT_TUNER_PORT`
- `SCRIPT_TUNER_MAX_INPUT_CHARS`
- `SCRIPT_TUNER_MAX_INPUT_TOKENS`
- `SCRIPT_TUNER_MAX_NEW_TOKENS`
- `SCRIPT_TUNER_NUM_BEAMS`
- `SCRIPT_TUNER_DO_SAMPLE`
- `SCRIPT_TUNER_TEMPERATURE`
- `SCRIPT_TUNER_TOP_P`
- `SCRIPT_TUNER_REPETITION_PENALTY`
- `HF_TOKEN` or `HUGGINGFACE_HUB_TOKEN`
