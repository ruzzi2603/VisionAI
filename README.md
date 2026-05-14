# VisionGuard AI

Sistema inteligente de monitoramento por câmeras com IA, análise de comportamento, alertas em tempo real, gravação de evidências e dashboard web.

## 🚀 Visão geral
O VisionGuard AI combina um backend Django + Django REST Framework com WebSockets, um frontend React/Vite e um pipeline de visão computacional em Python. O projeto é ideal para monitoramento de portões, entradas, recepções, lojas e outros ambientes sensíveis.

## ✨ Principais recursos
- Painel de controle para visualizar câmeras, alertas e métricas
- Detecção de pessoas, objetos suspeitos e comportamentos anômalos
- Captura de imagem e gravação de vídeo apenas durante incidentes
- Suporte a streaming MJPEG ao vivo para cada câmera
- Integração com telegram para alertas
- API de ingestão para pipeline de visão

## 🧩 Tecnologias
- Backend: Python 3.11, Django 5, Django REST Framework, Django Channels
- Frontend: React, Vite, Tailwind CSS
- Visão: OpenCV, Ultralytics YOLO, PyTorch
- Banco: SQLite (por padrão), compatível com PostgreSQL
- Comunicação em tempo real: WebSockets

## 📁 Estrutura do projeto
- `backend/` — API Django, modelos, autenticação, câmeras, eventos e alertas
- `frontend/` — aplicação React/Vite para dashboard
- `vision/` — pipeline de captura, detecção e ingestão de eventos
- `docs/` — documentação adicional do projeto

## ⚙️ Pré-requisitos
- Windows 10/11
- Python 3.11
- Node.js 18+ / npm
- Git

## 🛠️ Configuração local (Windows)
1. Clone o repositório:
```cmd
cd C:\Users\mathe\camera
git clone <URL_DO_REPOSITÓRIO> visionguard-ai
cd visionguard-ai
```

2. Crie e ative o ambiente Python para o backend:
```cmd
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Instale dependências do frontend:
```cmd
cd ..\frontend
npm install
```

4. Crie o arquivo de ambiente:
```cmd
cd ..
copy .env.example .env
```

5. Ajuste variáveis em `.env` conforme necessário.

## 🧪 Inicializar o backend
```cmd
cd backend
.venv\Scripts\activate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application
```
> Se quiser apenas desenvolvimento rápido, `python manage.py runserver 0.0.0.0:8000` também funcionará, mas use Daphne para suporte completo a WebSockets.

## 🌐 Inicializar o frontend
```cmd
cd frontend
npm run dev
```

## 📷 Inicializar pipeline de visão
```cmd
cd vision
python main.py
```

## 🔧 Configuração da ingestão de vídeo
No arquivo `.env` do projeto, defina:
```env
VISION_API_URL=http://127.0.0.1:8000/api/events/ingest/
VISION_INGEST_TOKEN=visionguard-local-token
VISION_CAMERA_CODE=CAM-001
```

## ✅ Como usar
1. Acesse o backend em `http://localhost:8000`.
2. Acesse o painel em `http://localhost:5173`.
3. Crie ou detecte câmeras via API/Dashboard.
4. Inicie o pipeline em `vision/main.py`.
5. Verifique eventos, alertas e evidências no dashboard.

## 📌 Endpoints principais
- `POST /api/auth/login/`
- `POST /api/auth/register/`
- `GET /api/auth/me/`
- `GET /api/dashboard/stats/`
- `CRUD /api/cameras/`
- `POST /api/cameras/discover_local/`
- `POST /api/cameras/{id}/ping/`
- `GET /api/cameras/{id}/signed_live_url/`
- `GET /api/cameras/{id}/live/?sig=...`
- `POST /api/events/ingest/`
- `CRUD /api/events/`
- `CRUD /api/alerts/`
- `CRUD /api/suspects/`
- `WS /ws/alerts/`

## 📘 Documentação adicional
Veja `DOCUMENTATION.md` e a pasta `docs/` para detalhes de arquitetura, fluxos e integrações.

## 🛡️ Segurança
Consulte `SECURITY.md` para o processo de reportar vulnerabilidades e recomendações de uso seguro.

## 🤝 Contribuição
Se quiser contribuir, leia `CONTRIBUTING.md` antes de enviar PRs.

## 📝 Licença
Licenciado sob a licença MIT. Consulte `LICENSE`.
