# API Surface

Base URL: `/api/v1`

- `GET /system/preflight`
- `POST /auth/login`
- `GET /cases`
- `POST /cases`
- `GET /cases/{case_id}`
- `POST /cases/{case_id}/documents/upload`
- `GET /cases/{case_id}/documents`
- `POST /cases/{case_id}/documents/{document_id}/process-ocr`
- `POST /cases/{case_id}/documents/{document_id}/build-evidence`
- `POST /cases/{case_id}/documents/{document_id}/map-fact-find`
- `GET /cases/{case_id}/documents/{document_id}/jobs`
- `GET /cases/{case_id}/fact-find/current`
- `POST /cases/{case_id}/fact-find/apply-preview`
- `POST /cases/{case_id}/calculator/auto-populate`
- `POST /cases/{case_id}/calculator/run`
- `GET /cases/{case_id}/calculator/results`

Job endpoints return queued responses shaped for future async orchestration.
