# ADR-002: PostgreSQL RLS untuk Tenant Isolation

**Status:** Accepted
**Date:** 2026-06-10

## Context
Multi-tenant CRM wajib mengisolasi data antar tenant. Pendekatan naif
(`WHERE tenant_id = ?`) rawan human error dan tidak memberi jaminan di level DB.

## Decision
Gunakan PostgreSQL Row-Level Security (RLS) sebagai defense-in-depth.
Setiap request set `app.current_tenant_id`; RLS policy otomatis memfilter
semua SELECT/INSERT/UPDATE/DELETE.

## Benefit
- Isolasi dijamin di level database, bukan hanya aplikasi.
- Tidak perlu mengingat `WHERE tenant_id` di setiap query.
- Mencegah kebocoran data antar tenant akibat bug aplikasi.
- Nilai jual kuat untuk keamanan/compliance saat menjual ke enterprise.

## Trade-off
- Perlu set session variable di setiap koneksi (overhead kecil).
- Migrasi dan operasi admin lebih kompleks (perlu bypass policy terkontrol).
- Testing lebih rumit (harus set tenant context di fixture).
- Sedikit overhead performa (dimitigasi indexing pada tenant_id).

## Alternatives Considered
- Schema-per-tenant — overhead terlalu besar untuk free tier.
- Database-per-tenant — biaya tinggi, kompleksitas operasional.
- WHERE clause manual — tidak aman, rawan lupa.
