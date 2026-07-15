# ADR-009: Modul Reporting & KPI (Operational Analytics)

**Status:** Accepted
**Date:** 2026-06-10

## Context
Dashboard yang sudah direncanakan hanya menampilkan metrik ringkas (conversion
rate, deals by owner, revenue forecast). Untuk produk CRM yang serius — apalagi
bila dijual — dibutuhkan kapabilitas reporting operasional dan KPI yang lebih
lengkap, dapat difilter per periode/owner/tim, dan dapat diekspor.

## Decision
Tambahkan modul `reporting` sebagai modul tersendiri (mengikuti layering
ADR-007). Modul ini READ-ONLY terhadap data modul lain — mengakses data lewat
contract (Protocol) modul terkait, bukan query langsung ke tabel modul lain.

Empat kategori KPI:
1. Sales performance — revenue, win rate, average deal size, sales cycle length,
   leaderboard per rep.
2. Activity & productivity — activities per user, response time ke lead baru,
   task completion rate, email open/click rate.
3. Pipeline health — conversion per stage, stage duration (bottleneck),
   weighted forecast, stale & at-risk deals.
4. AI effectiveness — akurasi deal scorer (predicted vs actual), follow-up
   approval & conversion rate, LLM cost/token per tenant, chatbot deflection.

Output: tampilan report dengan filter, plus ekspor CSV/Excel. Agregasi berat
dijalankan sebagai job terjadwal (Celery beat) dan disimpan ke tabel ringkasan
(`report_snapshots`) agar dashboard cepat.

## Benefit
- Memberi nilai nyata bagi manajer sales (insight, bukan sekadar data mentah).
- Diferensiasi produk: KPI AI effectiveness jarang ada di CRM lain.
- Materialized/snapshot approach menjaga performa walau data besar.
- Modul read-only via contract menjaga batas arsitektur tetap bersih.

## Trade-off
- Menambah modul dan tabel ringkasan (kompleksitas + storage).
- Job agregasi terjadwal menambah beban worker dan perlu dipantau.
- Snapshot bisa basi antar interval; perlu kompromi antara real-time vs biaya.
- Reporting lintas modul harus disiplin lewat contract agar tidak bocor coupling.

## Catatan Implementasi
- Tabel `report_snapshots(tenant_id, report_type, period, payload JSONB, generated_at)`.
- Beat job harian/mingguan mengisi snapshot per tenant.
- Query real-time hanya untuk rentang kecil; rentang besar pakai snapshot.
- Semua akses data antar modul lewat Protocol (mis. `DealContractProtocol`).

## Alternatives Considered
- Hanya dashboard (status quo) — ditolak: tidak cukup untuk produk komersial.
- Query langsung ke tabel modul lain — ditolak: melanggar batas modul (ADR-007).
- BI tool eksternal (Metabase/Superset) — dipertimbangkan untuk masa depan,
  namun untuk MVP komersial reporting in-app lebih terkontrol dan terintegrasi.
