# ADR-001: LiteLLM sebagai LLM Abstraction Layer

**Status:** Accepted
**Date:** 2026-06-10

## Context
PranataCRM punya 4 AI agents yang semuanya memanggil LLM. Saat dev butuh model
lokal gratis; saat produksi butuh performa dengan biaya terkontrol. Tanpa
abstraction, ganti provider berarti ubah kode di 4 agent.

## Decision
Gunakan LiteLLM sebagai unified interface ke semua provider.
- Dev: `ollama/llama3.1:8b` (lokal, gratis, offline)
- Prod: `groq/llama-3.1-8b-instant` (free tier 14.4k req/hari)
- Fallback: `openrouter/mistralai/mistral-7b-instruct`

## Benefit
- Satu API untuk semua provider; ganti provider cukup ubah env variable.
- LiteLLM menangani retry, timeout, dan normalisasi response.
- Mudah menambah Anthropic/OpenAI di masa depan tanpa refactor agent.
- Bebas vendor lock-in — argumen kuat untuk calon pembeli enterprise.

## Trade-off
- Menambah satu dependency dan satu lapis abstraksi (debug sedikit lebih jauh).
- Bergantung pada stabilitas API LiteLLM; perubahan upstream bisa berdampak.
- Fitur spesifik provider tertentu mungkin tidak ter-expose seragam.

## Alternatives Considered
- Direct Groq SDK — vendor lock-in, harus refactor saat ganti provider.
- OpenAI SDK (kompatibel Groq) — dukungan Ollama kurang baik.
- Custom abstraction — over-engineering untuk scope ini.
