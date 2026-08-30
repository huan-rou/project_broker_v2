# Providers

The thin slice keeps real provider integration behind explicit configuration.

Required environment variables:

- `OCR_PROVIDER`
- `OCR_API_KEY`
- `LLM_PROVIDER`
- `LLM_API_KEY`

When these are missing, OCR and bridge jobs return structured failures instead of silently using fake extraction.
