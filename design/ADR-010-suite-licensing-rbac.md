# ADR-010: Suite Licensing & RBAC Model (Hybrid Role, Custom Permission, Hard Limit)

**Status:** Accepted
**Date:** 2026-06-10
**Berlaku untuk:** Otorisasi & licensing lintas Pranata Suites (CRM, Docs, dst)

## Context
Satu tenant dapat berlangganan beberapa app dalam Pranata Suites dengan jumlah
seat berbeda per app. Satu user adalah satu identitas, namun aksesnya ke tiap
app ditentukan oleh seat. Di dalam tiap app perlu RBAC sendiri (mis. sales
manager bisa Reporting KPI, sales staff tidak). Tenant juga ingin membuat role
sendiri.

## Decision
Terapkan tiga lapis otorisasi:
1. Suite identity — tenant, user, suite_role (kapabilitas lintas-suite: billing,
   seat, user, role management).
2. Seat licensing per app — `app_subscriptions.seats_purchased` membatasi jumlah
   `app_seats` aktif per (tenant, app). Akses app = menempati seat aktif.
3. RBAC per app — role per app berisi permission dari katalog yang dimiliki app.
   Role diberikan terikat pada seat (`user_roles → app_seat`).

Keputusan spesifik:
- Role = **Hybrid**: suite role (global) + app role (per app, independen).
- Permission = **Custom roles**: tenant admin membuat role & memilih permission
  dari katalog yang didefinisikan app (permission catalog dikontrol app).
- Licensing = **Hard limit** untuk MVP: seat penuh → tolak; overage = roadmap.
- Lisensi dihitung **per seat per app**: user di 2 app memakai 2 seat.

## Benefit
- Pemisahan jelas: identity vs licensing vs RBAC — mudah dipahami & diuji.
- Fleksibel untuk berbagai struktur organisasi (custom role) — nilai jual.
- Aman: permission catalog dikontrol app, tenant tak bisa mengarang permission.
- Role terikat seat → mustahil salah pasang role lintas app; cabut seat otomatis
  menon-aktifkan role app itu.
- Suite-aware sejak awal → selaras dengan SSO bertahap (ADR-004).

## Trade-off
- Lebih banyak tabel & konsep (subscription, seat, role, permission, mapping).
- Penegakan seat harus atomik (lock baris subscription) untuk hindari race.
- Permission efektif perlu di-cache + invalidasi saat role/seat berubah.
- Hard limit bisa menambah friksi onboarding (mitigasi: pesan jelas + ajakan upgrade).

## Catatan Implementasi
- `user_roles` menunjuk `app_seat`, bukan `user` global.
- Hitung & batasi seat dalam transaksi dengan SELECT ... FOR UPDATE pada subscription.
- Endpoint dilindungi dua dependency: require_app_access (seat) lalu
  require_permission (RBAC).
- Tabel otorisasi tenant-scoped + RLS; relasi soft reference (no-FK) + index manual.

## Alternatives Considered
- Role global seragam lintas app — ditolak: tidak fleksibel (mis. manager di CRM
  belum tentu setara di Docs).
- Fixed roles saja — ditolak: kurang fleksibel untuk produk komersial.
- Soft limit/overage sejak MVP — ditunda: butuh metering & integrasi billing
  lebih kompleks; hard limit lebih sederhana & aman untuk awal.
- Role diberikan langsung ke user (bukan via seat) — ditolak: memungkinkan role
  app "menggantung" tanpa seat, rawan inkonsistensi.
