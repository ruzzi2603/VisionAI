# Solução de Problemas

## Problemas comuns

### 1. Python ou dependências não instaladas
- Verifique se está usando Python 3.11.
- Ative o ambiente virtual antes de instalar pacotes.
- Rode `pip install -r backend/requirements.txt`.

### 2. Erro `ModuleNotFoundError: No module named 'cv2'`
- Confirme que o ambiente virtual está ativado.
- Instale `opencv-python` em `backend/.venv`.
- Exemplo:
  ```cmd
  cd backend
  .venv\Scripts\activate
  pip install opencv-python
  ```

### 3. Câmera aparece offline
- Verifique a fonte em `stream_url` ou `source` no registro da câmera.
- Utilize `POST /api/cameras/{id}/ping/` no backend para atualizar o status.
- Confirme se outra aplicação não está usando a câmera.

### 4. Live stream não carrega
- Verifique se o backend está rodando em `http://localhost:8000`.
- Garanta que `signed_live_url` é gerado antes de abrir o stream.
- No frontend, use o botão `Ver ao vivo` e permita o carregamento de imagem MJPEG.

### 5. Evento de ingestão retorna erro no backend
- Cheque `VISION_CAMERA_CODE` em `.env` e o `camera_code` cadastrado no backend.
- Valide `VISION_INGEST_TOKEN` e o header `X-Vision-Token` na pipeline.
- Confirme que o endpoint `/api/events/ingest/` está acessível.

### 6. Modelo YOLO corrompido ou falhando ao carregar
- Verifique se o arquivo `yolov8n.pt` foi baixado corretamente.
- Se o download falhar, apague o arquivo e execute novamente.
- Use o caminho correto em `YOLO_MODEL_PATH` no `.env` ou `vision/main.py`.

## Diagnóstico rápido
- Backend: `python manage.py runserver` ou `python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application`
- Frontend: `npm run dev`
- Pipeline de visão: `python vision/main.py`

## Contato para suporte
- Abra uma issue com título claro.
- Inclua logs, comandos e comportamento esperado.
