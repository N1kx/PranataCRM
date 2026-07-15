# ADR-004: SSO Strategy untuk Pranata Suites (Bertahap)

**Status:** Partially Accepted (Phase 1 implemented)
**Date:** 2026-10-06

## Context
PranataCRM adalah app pertama Pranata Suites. Akan ada PranataDMS dan app lain.
Semua harus terhubung lewat single sign-on agar user tidak login ulang per app.

## Decision
Bertahap:
- Phase 1 (sekarang): auth mandiri di `app/core/auth.py`, semua logic diisolasi.
- Phase 2 (saat DMS mulai): extract ke `pranata-shared/auth-service`,
  OAuth2 Authorization Code Flow, CRM & DMS jadi OAuth clients.

## Benefit
- Phase 1 cepat dikerjakan, tidak over-engineer untuk satu app.
- Isolasi auth memudahkan ekstraksi ke service bersama nanti.
- Phase 2 memberi true SSO: login sekali untuk semua app dalam suite.

## Trade-off
- Phase 1 menimbulkan technical debt: nanti perlu migrasi users ke shared auth.
- Phase 2 lebih kompleks: kelola OAuth client credentials per app,
  sinkronisasi token lifetime antar app.

## Migration Path
Deploy auth-service → migrasi users → ubah `auth.py` jadi OAuth client →
ulangi untuk DMS.

## Alternatives Considered
- Langsung bangun SSO penuh sekarang — over-engineering, memperlambat MVP CRM.
- Shared auth library (bukan service) — lebih simpel tapi bukan true SSO.
