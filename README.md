# Script Tuner Inference
사용 모델: Fine-tuned T5Gemma2 
기능: 비영어권 화자가 작성한 OPIc 영어 스크립트를  보다 자연스러운 구어체 영어로 첨삭한다.

## Environment
본 서비스는 python venv 기반 환경에서 작동한다.  
python 환경이 설치되어 있어야 한다.  
가상환경 설정, 패키지 설치 작업 때문에 처음 실행할 땐 로딩이 좀 느리다.

## Run
1. 폴더 내 Start ScriptTuner 배치 파일을 실행한다.  
2. ui가 실행되면, 자동으로 모델을 로드한다. 모델 로드 스테이터스은 왼쪽 아래 파란 버튼 아래에 표시된다.
3. 모델 로드 이전에, 직접 토큰을 입력할 필요가 있다. 스테이터스에 토큰을 입력한다.
4. 이후 로딩이 완료되면 왼쪽 창에 변환할 스크립트를 입력하고 '변환' 버튼을 클릭한다.
5. 잠깐의 로딩 후 오른쪽 창에 변환 완료된 스크립트가 출력된다.

## HuggingFace
HuggingFace private/gated 모델 접근을 위해 토큰이 필요하다.  
모델: [T5Gemma 2 1B casual](https://huggingface.co/aip-scripttuner-team)

토큰은 서비스 실행 후 ui  내에서 직접 입력하거나 터미널 창에서 다음 코드를 통해 환경변수로 직접 입력할 수 있다.

```powershell
$env:HF_TOKEN="hf_..."
```

실제 모델 repo id를 알고 있다면 다음 코드를 통해 모델을 미리 지정해놓을 수도 있다.

```powershell
$env:SCRIPT_TUNER_MODEL_ID="aip-scripttuner-team/your-model-repo"
```
