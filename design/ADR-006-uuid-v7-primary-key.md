# ADR-006: UUID v7 sebagai Primary Key (Application-Generated, Kompatibel PostgreSQL ≤15)

**Status:** Accepted
**Date:** 2026-06-10
**Deciders:** Niko Winoko
**Berlaku untuk:** Seluruh tabel pada skema database PranataCRM

---

## Context

PranataCRM adalah multi-tenant CRM yang dirancang sebagai modular monolith
dengan kesiapan migrasi ke microservice. Pemilihan tipe primary key berdampak
pada keamanan (enumerability), performa index, kemudahan distribusi ID, dan
portabilitas antar database.

Dua kandidat utama:
- BIGINT auto-increment: performa index optimal, hemat storage, tapi
  enumerable (rawan IDOR) dan butuh koordinasi DB untuk generate ID.
- UUID v4: tidak enumerable dan bisa di-generate tanpa DB, tapi nilainya
  acak sehingga menyebabkan fragmentasi index B-tree (insert acak ke
  berbagai posisi page) dan write amplification.

Kendala tambahan: deployment menargetkan **PostgreSQL versi 15 atau di
bawahnya** (mis. Railway/Supabase yang belum tentu PostgreSQL 17). Fungsi
`uuidv7()` built-in baru hadir di PostgreSQL 18, dan `gen_random_uuid()`
hanya menghasilkan v4. Maka generasi UUID v7 **tidak boleh** bergantung pada
fungsi database.

## Decision

Gunakan **UUID v7 yang di-generate di application layer (Python)** sebagai
primary key untuk semua tabel.

Alasan UUID v7:
- Time-ordered (48 bit pertama = Unix timestamp milidetik), sehingga nilai
  monotonically increasing — insert selalu mendekati ujung B-tree, performa
  index dan write mendekati BIGINT.
- Tetap tidak enumerable (bagian acak 74 bit) — aman untuk multi-tenant.
- Bisa di-generate tanpa round-trip ke DB — cocok untuk arsitektur terdistribusi.

Generasi dilakukan di Python (bukan DB) agar kompatibel dengan PostgreSQL ≤15:
kolom bertipe `UUID` biasa, nilai default diisi oleh aplikasi via
`default=uuid7` pada SQLAlchemy model. Tidak ada dependensi pada fungsi
database apa pun.

### Implementasi

Kolom database (kompatibel semua versi PostgreSQL yang punya tipe `uuid`):

```sql
-- Tipe uuid sudah ada sejak PostgreSQL lama; tidak perlu uuidv7() built-in
id UUID PRIMARY KEY    -- nilai diisi aplikasi, BUKAN DEFAULT dari DB
```

Generator di application layer:

```python
# app/shared/types.py
import os
import time
import uuid

def uuid7() -> uuid.UUID:
    """
    Generate UUID v7 (time-ordered) di application layer.
    Tidak bergantung pada fungsi database, jadi kompatibel dengan
    PostgreSQL 15 ke bawah.

    Layout (RFC 9562):
      - 48 bit  : unix timestamp milidetik
      - 4 bit   : version (0b0111 = 7)
      - 12 bit  : random_a
      - 2 bit   : variant (0b10)
      - 62 bit  : random_b
    """
    unix_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = int.from_bytes(os.urandom(10), "big")  # 80 bit acak

    # rakit 128 bit
    value = unix_ms << 80
    value |= (0x7 << 76)                       # version 7
    value |= ((rand >> 68) & 0x0FFF) << 64     # 12 bit random_a
    value |= (0b10 << 62)                       # variant
    value |= (rand & ((1 << 62) - 1))           # 62 bit random_b
    return uuid.UUID(int=value)
```

Pemakaian di SQLAlchemy model:

```python
# app/models/base.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.shared.types import uuid7
import uuid

class Base(DeclarativeBase):
    pass

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid7,        # generate di Python saat insert
    )
```

Catatan kompatibilitas:
- Jika suatu saat pindah ke PostgreSQL 18+, generasi tetap bisa di app layer
  tanpa perubahan. Migrasi ke `DEFAULT uuidv7()` bersifat opsional, bukan
  keharusan.
- Untuk menghindari menulis generator sendiri, boleh memakai library
  `uuid6`/`uuid7` dari PyPI (`pip install uuid6`), yang menyediakan `uuid7()`.
  Implementasi inline di atas disertakan agar tidak ada ketergantungan wajib.

## Consequences

### Positif
- Performa index dan write mendekati BIGINT karena nilai sequential.
- Tidak enumerable — endpoint seperti `/contacts/{id}` tidak bisa ditebak.
- ID dapat dibuat di aplikasi tanpa round-trip DB — siap untuk distribusi
  dan microservice (ID unik lintas service tanpa koordinasi).
- Portabel: kompatibel PostgreSQL 15 ke bawah karena tidak pakai `uuidv7()` DB.
- Konsisten dengan keputusan no-FK (ADR-005): ID yang dapat di-generate di
  aplikasi memudahkan pembuatan record dan relasi tanpa bergantung pada DB.

### Negatif (dan mitigasinya)
- Storage 16 byte per ID vs 8 byte BIGINT → dampak kecil pada skala project ini;
  diterima demi keamanan dan distribusi.
- Timestamp pada UUID v7 sedikit membocorkan waktu pembuatan record. Untuk CRM
  internal ini bukan masalah; jika sensitif, jangan ekspos ID ke pihak yang
  tidak berkepentingan.
- Bergantung pada jam sistem yang benar. Mitigasi: pastikan NTP aktif di server.
- Generator buatan sendiri perlu unit test untuk memverifikasi versi/variant
  bit dan urutan monotonic.

## Aturan Implementasi

1. Semua PK memakai tipe `UUID` dengan `default=uuid7` di model — JANGAN pakai
   `gen_random_uuid()` (itu v4) maupun `DEFAULT uuidv7()` DB (tidak ada di ≤15).
2. Semua kolom soft reference (lihat ADR-005) juga bertipe `UUID`.
3. Sediakan unit test untuk `uuid7()`: cek version=7, variant=0b10, dan bahwa
   dua ID berurutan menjaga urutan waktu (monotonic non-decreasing).

## Alternatives Considered

1. **BIGINT auto-increment** — ditolak: enumerable, butuh koordinasi DB,
   menyulitkan distribusi/microservice.
2. **UUID v4** — ditolak: fragmentasi index dan write amplification akibat
   nilai acak.
3. **UUID v7 via `uuidv7()` DB** — ditolak: tidak tersedia di PostgreSQL ≤15
   (baru ada di 18), melanggar target portabilitas.
4. **ULID** — dipertimbangkan (juga time-ordered), tapi UUID v7 dipilih karena
   tipe `uuid` native PostgreSQL dan dukungan tooling yang lebih luas.
