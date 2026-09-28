# Render 배포 안내

이미지를 업로드하면 Sobel 엣지 검출 결과(PNG)를 보여주고 다운로드할 수 있는 Flask 웹 서비스를 Render 무료 플랜에 배포하는 방법입니다.

## 프로젝트 구성

| 파일 | 역할 |
|---|---|
| `app.py` | Flask 서버 (`/`, `/api/edge`, `/healthz`) |
| `edge_detector.py` | Sobel 엣지 검출 (numpy + Pillow) |
| `templates/index.html`, `static/` | 업로드 화면 |
| `requirements.txt` | 의존성 (Flask, gunicorn, numpy, Pillow) |
| `.python-version` | Render에서 사용할 Python 버전 (`3.12`) |
| `render.yaml` | Render Blueprint 설정 |

## 1. 로컬에서 먼저 확인하기

```bash
python -m pip install -r requirements.txt
python app.py
```

브라우저에서 http://localhost:5000 에 접속해 이미지를 올려 봅니다.
(gunicorn은 Windows에서 실행되지 않으므로 로컬에서는 `python app.py`로 실행합니다.)

엣지 검출만 따로 실행할 수도 있습니다.

```bash
python edge_detector.py 입력.jpg 결과.png
```

## 2. GitHub에 올리기

Render는 GitHub(또는 GitLab, Bitbucket) 저장소에서 코드를 가져와 배포합니다.

1. GitHub에서 새 저장소를 만듭니다 (예: `sobel-edge-detection`).
2. 프로젝트 폴더에서 다음을 실행합니다.

```bash
git init
git add .
git commit -m "Sobel edge detection web service"
git branch -M main
git remote add origin https://github.com/<내-아이디>/sobel-edge-detection.git
git push -u origin main
```

`app.py`, `edge_detector.py`, `templates/`, `static/`, `requirements.txt`, `.python-version`, `render.yaml`이 모두 저장소 최상위에 있어야 합니다.

## 3. Render에서 배포하기

### 방법 A: Blueprint 사용 (권장)

`render.yaml`에 설정이 모두 들어 있어서 클릭 몇 번이면 끝납니다.

1. https://dashboard.render.com 에 로그인합니다 (GitHub 계정으로 가입 가능).
2. **New → Blueprint**를 선택합니다.
3. 방금 만든 저장소를 연결합니다.
4. `sobel-edge-detection` 서비스가 표시되면 **Apply**를 누릅니다.

### 방법 B: Web Service 직접 만들기

1. **New → Web Service** → 저장소를 선택합니다.
2. 다음과 같이 입력합니다.

| 항목 | 값 |
|---|---|
| Language | Python 3 |
| Branch | `main` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120` |
| Instance Type | Free |

3. **Advanced → Health Check Path**에 `/healthz`를 입력합니다.
4. **Create Web Service**를 누릅니다.

### 배포 확인

- 빌드 로그에 `Your service is live`가 나오면 완료입니다. 보통 2~5분 걸립니다.
- `https://<서비스이름>.onrender.com` 에 접속해 이미지를 올려 봅니다.
- `https://<서비스이름>.onrender.com/healthz` 에 접속하면 `ok`가 표시됩니다.

이후에는 `main` 브랜치에 push할 때마다 자동으로 다시 배포됩니다.

## 4. 알아두면 좋은 점

**Python 버전**
`.python-version` 파일 때문에 Render는 Python 3.12.x를 사용합니다. 버전을 바꾸려면 이 파일을 수정하거나, 환경 변수 `PYTHON_VERSION`(예: `3.12.8`)을 설정하세요. 환경 변수가 파일보다 우선합니다.

**첫 접속이 느린 경우 (무료 플랜)**
무료 플랜은 15분 동안 요청이 없으면 서버가 잠듭니다. 그 뒤 첫 접속은 서버가 깨어나는 동안 30초~1분 정도 걸립니다. 그 다음 요청부터는 정상 속도입니다.

**메모리와 워커 수**
무료 플랜의 메모리는 512MB입니다. 4000×4000 크기 이미지를 처리하면 요청 하나가 순간적으로 약 320MB를 사용하므로 워커를 1개로 설정했습니다. 유료 플랜(메모리 2GB 이상)으로 바꾸면 `--workers 2` 이상으로 늘려도 됩니다.

**업로드 제한**
- 최대 10MB, jpg / jpeg / png / bmp / gif / webp / tiff만 허용합니다.
- 긴 변이 4000px보다 큰 이미지는 비율을 유지한 채 4000px로 줄여서 처리합니다.
- 이미지는 메모리에서만 처리하고 서버 디스크에 저장하지 않습니다.

## 5. 문제 해결

| 증상 | 확인할 것 |
|---|---|
| 빌드 실패 | 빌드 로그의 pip 오류를 확인합니다. `requirements.txt`가 저장소 최상위에 있는지 확인합니다. |
| `ModuleNotFoundError: edge_detector` | `edge_detector.py`가 push되었는지 확인합니다. |
| 배포 후 계속 `Deploy failed` (health check) | Start Command에 `--bind 0.0.0.0:$PORT`가 있는지, Health Check Path가 `/healthz`인지 확인합니다. |
| 큰 이미지에서 502 오류 또는 재시작 | 메모리 부족입니다. Logs에서 `Out of memory`를 확인합니다. 더 작은 이미지를 쓰거나 유료 플랜으로 올리세요. |
| 업로드 시 "파일이 너무 큽니다" | 10MB 제한입니다. `app.py`의 `MAX_UPLOAD_MB` 값으로 조정할 수 있습니다. |
