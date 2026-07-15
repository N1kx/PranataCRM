# ADR-005: Tanpa Foreign Key Constraint (Soft Reference)

**Status:** Accepted
**Date:** 2026-06-10
**Deciders:** Niko Winoko
**Context modul:** Berlaku untuk seluruh skema database PranataCRM

---

## Context

PranataCRM menggunakan arsitektur modular monolith di mana antar modul
berinteraksi melalui contract (Protocol), bukan melalui dependency database
langsung. Untuk menjaga konsistensi prinsip ini dan mempersiapkan migrasi
ke microservice di masa depan, kami mengevaluasi penggunaan FOREIGN KEY constraint.

Pengalaman sebelumnya pada project ERP berjalan baik tanpa FK. Coding dan QA
project ini akan dibantu oleh AI, yang berarti volume kode yang dihasilkan tinggi
dan butuh pattern yang konsisten serta mudah direplikasi.

## Decision

**Tidak menggunakan FOREIGN KEY constraint sama sekali.** Semua relasi antar
tabel disimpan sebagai kolom UUID biasa (soft reference). Referential integrity
dipindahkan sepenuhnya ke application layer melalui tiga pilar:

1. **Write Guard** — validasi referensi sebelum insert/update via
   `ReferenceValidator`. Dalam modul: cek via repository. Lintas modul: cek via contract.

2. **Delete Cascade** — cleanup child records dilakukan eksplisit melalui
   domain events (`EventBus`). Parent mem-publish event delete; modul pemilik
   child men-subscribe dan membersihkan datanya sendiri.

3. **Orphan Sweeper** — Celery beat job harian yang scan orphaned records
   sebagai jaring pengaman terakhir, sekaligus sinyal kualitas (jika sering
   menemukan orphan, berarti ada bug di pilar 1/2).

## Consequences

### Positif
- Konsistensi penuh dengan prinsip "modul berinteraksi via contract"
- Boundary modul bisa berubah tanpa migration drop-constraint yang berisiko
- Migrasi ke microservice mulus — tidak ada FK lintas-service yang perlu dibongkar
- Tabel high-volume (activities, ai_tasks) bebas dipartisi/shard kapan saja
- Write lebih cepat tanpa constraint check
- Pattern write-guard konsisten, mudah direplikasi oleh AI saat generate kode

### Negatif (dan mitigasinya)
- Database tidak lagi menjamin integrity → dimitigasi 3 pilar di atas
- Cleanup jadi tanggung jawab aplikasi → dimitigasi domain events + sweeper
- Risiko orphan jika handler gagal → dimitigasi orphan sweeper harian
- **Index harus dibuat manual** untuk SETIAP kolom soft reference, karena
  tidak ada index otomatis dari FK. Ini WAJIB, bukan opsional.

## Aturan Implementasi (untuk konsistensi AI-generated code)

1. Setiap method `create_*` dan `update_*` yang menyimpan referensi WAJIB
   memanggil `ReferenceValidator.ensure_exists` di awal.
2. Setiap method `delete_*` pada entitas yang punya child WAJIB mem-publish
   domain event yang sesuai.
3. Setiap modul yang menyimpan referensi ke entitas modul lain WAJIB
   men-subscribe event delete entitas tersebut.
4. Setiap kolom UUID yang menyimpan referensi WAJIB punya index manual.
5. Setiap relasi baru WAJIB ditambahkan ke query orphan sweeper.

## Alternatives Considered

1. **Hybrid (FK dalam modul, soft ref lintas modul)** — ditolak karena
   menambah pengecualian yang harus diingat; tidak konsisten.
2. **Full FK** — ditolak karena bertentangan dengan prinsip modular dan
   menyulitkan migrasi microservice.

## Catatan

Keputusan ini menukar "jaminan gratis dari database" dengan "kontrol penuh
di application layer plus kewajiban membangun safety net sendiri". Trade-off
ini diterima secara sadar dan didokumentasikan agar setiap kontributor
(termasuk AI) memahami konsekuensi dan aturan implementasinya.
