# PranataCRM — Rancangan RBAC & Suite Licensing

> Dokumen desain terpisah untuk otorisasi, seat licensing, dan kontrol akses
> dalam konteks Pranata Suites. Berdiri sendiri dari ringkasan teknis utama.
>
> Keputusan desain (sesuai konfirmasi):
> - Role: **Hybrid** — ada suite role + role khusus per-app.
> - Permission: **Custom roles** — tenant admin bisa bikin role & atur permission.
> - Licensing: **Hard limit** untuk MVP (overage = roadmap).

---

## Daftar Isi
1. Masalah & Tujuan
2. Konsep Tiga Lapis Otorisasi
3. Studi Kasus: Tenant 1020
4. Model Data
5. Suite Role vs App Role (Hybrid)
6. Custom Roles & Permission Catalog
7. Seat Licensing (Hard Limit)
8. Alur Otorisasi pada Request
9. Implementasi (FastAPI)
10. Integrasi dengan Keputusan Arsitektur Lain
11. Roadmap (Overage, dll)
12. Edge Cases & Aturan

---

## 1. Masalah & Tujuan

Dalam Pranata Suites, satu organisasi (tenant) bisa berlangganan beberapa
aplikasi (CRM, Docs, dst). Kebutuhan:

- Satu tenant membeli sejumlah seat per aplikasi (mis. 6 seat CRM, 6 seat Docs).
- Satu user adalah satu identitas di level suite, tapi belum tentu punya akses
  ke semua aplikasi. Beberapa user hanya CRM, beberapa hanya Docs, sebagian
  bersinggungan (punya akses keduanya).
- Di dalam tiap aplikasi ada RBAC sendiri: mis. sales manager bisa akses
  Reporting KPI di CRM, sales staff tidak.
- Tenant admin bisa membuat role sendiri dan mengatur permission-nya (custom).

Tujuan desain: memisahkan dengan jelas tiga pertanyaan berbeda:
1. Siapa user ini di organisasi? (identity)
2. Aplikasi mana yang boleh dia pakai? (licensing/seat)
3. Apa yang boleh dia lakukan di dalam aplikasi itu? (RBAC)

---

## 2. Konsep Tiga Lapis Otorisasi

**Lapis 1 — Suite Identity.**
Tenant (organisasi) memiliki banyak user. Satu user = satu identitas, login
sekali (SSO saat Pranata Suites matang; sebelum itu, identitas tetap
terpusat di level suite). User punya satu suite role (mis. tenant_owner atau
member) yang mengatur kapabilitas lintas-suite, seperti mengelola billing dan
mengundang user.

**Lapis 2 — Seat Licensing per App.**
Tenant berlangganan tiap aplikasi secara terpisah dengan jumlah seat tertentu.
Seat adalah "kursi berbayar" yang dialokasikan ke user. User hanya bisa membuka
aplikasi jika ia menempati seat aktif untuk aplikasi tersebut. Hard limit:
jika seat penuh, user berikutnya tidak bisa diberi akses sampai ada seat kosong
atau tenant menambah seat.

**Lapis 3 — RBAC per App.**
Di dalam tiap aplikasi, akses diatur oleh role yang berisi sekumpulan permission.
Role bersifat per-aplikasi dan independen: user bisa jadi "sales manager" di CRM
sekaligus "viewer" di Docs. Tenant admin dapat membuat custom role dan memilih
permission apa saja yang melekat.

Ketiga lapis ini dievaluasi berurutan pada setiap request: identitas valid →
punya seat untuk app ini → role-nya mengizinkan aksi ini.

---

## 3. Studi Kasus: Tenant 1020

Tenant 1020 membeli 6 seat CRM dan 6 seat Docs. Misalkan ada 11 user (A–K):

- User A–F → menempati seat PranataCRM (6 seat terpakai penuh).
- User F–K → menempati seat PranataDocs (6 seat terpakai penuh).
- User F → bersinggungan: menempati seat di CRM dan Docs sekaligus.

Total user unik = 11, namun total seat terpakai = 12 (karena user F memakai 2
seat, satu di tiap app). Ini penting: **lisensi dihitung per seat per app, bukan
per user unik**. Seorang user yang memakai dua app memakan dua seat.

Di dalam CRM:
- User A diberi role "sales manager" → boleh akses Reporting KPI.
- User B–E diberi role "sales staff" → tidak boleh akses Reporting KPI.
- User F diberi role "sales manager" juga (atau role lain sesuai kebutuhan).

Di dalam Docs (independen dari CRM):
- User F diberi role "viewer" → hanya bisa baca, walau di CRM dia manager.
- User G diberi role "editor" → bisa edit dokumen.

Jika tenant ingin menambah user ke CRM padahal 6 seat sudah penuh: ditolak,
dengan pesan untuk menambah seat (upgrade). Itulah hard limit.

---

## 4. Model Data

Tabel-tabel inti (mengikuti konvensi proyek: UUID v7, soft reference tanpa FK,
RLS per tenant). Tabel ini idealnya berada di domain identity/billing yang
dapat dipakai bersama oleh seluruh suite (lihat ADR-004 SSO bertahap).

| Tabel | Peran |
|---|---|
| tenants | organisasi |
| users | identitas user (level suite), punya suite_role |
| apps | katalog aplikasi suite (CRM, Docs, dst) |
| app_subscriptions | langganan tenant atas suatu app + jumlah seat |
| app_seats | alokasi seat: user mana menempati seat app mana |
| permissions | katalog permission per app |
| roles | role per app (system atau custom milik tenant) |
| role_permissions | permission apa saja yang dimiliki sebuah role |
| user_roles | role apa yang diberikan ke user pada seat app tertentu |

Ringkasan kolom penting:

```
apps
  id, code (mis. "crm", "docs"), name

app_subscriptions
  id, tenant_id, app_id, plan, seats_purchased, status, current_period_end

app_seats
  id, subscription_id, tenant_id, app_id, user_id, assigned_at, status
  -- unik per (app_id, user_id): satu user maksimal satu seat per app

permissions
  id, app_id, code (mis. "crm.reporting.view"), description

roles
  id, tenant_id (NULL untuk role sistem global), app_id, name,
  is_system (true = bawaan, tidak bisa dihapus), description

role_permissions
  role_id, permission_id

user_roles
  id, app_seat_id, role_id
  -- role diberikan terikat pada seat (app), bukan langsung ke user global
```

Catatan desain penting: `user_roles` menunjuk ke `app_seat`, bukan langsung ke
`user`. Dengan begitu role secara struktural selalu terikat pada aplikasi
tertentu — mustahil "salah pasang" role CRM ke konteks Docs, karena seat sudah
menentukan app-nya. Saat seat dicabut, role pada app itu otomatis tidak berlaku.

---

## 5. Suite Role vs App Role (Hybrid)

**Suite role** (di `users.suite_role`) mengatur kapabilitas lintas-suite:

| Suite role | Kapabilitas |
|---|---|
| tenant_owner | kelola billing & langganan, tambah/kurangi seat, kelola semua user, tunjuk admin |
| tenant_admin | kelola user & alokasi seat, kelola custom role; tidak kelola billing |
| member | user biasa; kapabilitas di dalam app ditentukan app role |

Suite role TIDAK menentukan apa yang bisa dilakukan di dalam CRM/Docs. Ia hanya
mengatur hal level-organisasi (billing, seat, user, role management).

**App role** (di `roles`, diberikan via `user_roles`) mengatur aksi di dalam
satu aplikasi. Contoh app role CRM: sales manager, sales staff, read-only.
Contoh app role Docs: editor, viewer. App role inilah yang memuat permission
seperti `crm.reporting.view`.

Mengapa hybrid: hal seperti "boleh menambah seat" atau "boleh membuat role
baru" adalah keputusan organisasi yang sama di semua app — cocok di suite role.
Sedangkan "boleh lihat reporting KPI" sangat spesifik per app — cocok di app role.
Memisahkan keduanya mencegah duplikasi dan kebingungan.

Interaksi keduanya: seorang tenant_owner tetap perlu menempati seat CRM dan
diberi app role untuk benar-benar memakai fitur CRM. Status owner memberinya
kuasa mengelola, bukan otomatis akses penuh ke setiap fitur app. (Opsional:
sistem bisa memberi owner sebuah app role "administrator" otomatis saat ia
menempati seat — keputusan produk, bukan keharusan arsitektur.)

---

## 6. Custom Roles & Permission Catalog

**Permission catalog** didefinisikan oleh tiap aplikasi (bukan oleh tenant).
Setiap app mendaftarkan permission-nya dengan kode yang konsisten. Contoh untuk
CRM:

```
crm.contact.view        crm.contact.create     crm.contact.update
crm.contact.delete      crm.deal.view          crm.deal.create
crm.deal.update         crm.deal.delete        crm.deal.change_stage
crm.activity.view       crm.activity.create
crm.reporting.view      crm.reporting.export
crm.ai.score_deal       crm.ai.followup_approve
crm.knowledge.manage    crm.settings.manage
```

Permission bersifat granular dan stabil. Aplikasi adalah pemilik daftar ini;
penambahan permission baru = bagian rilis app.

**Custom role** dibuat oleh tenant_admin/tenant_owner. Tenant memilih app,
memberi nama role, lalu mencentang permission mana saja yang melekat. Contoh:
tenant 1020 membuat role "sales manager" di CRM dengan permission termasuk
`crm.reporting.view` dan `crm.reporting.export`, lalu role "sales staff" tanpa
dua permission itu.

**System roles** disediakan bawaan (is_system = true) sebagai titik awal yang
praktis, mis. CRM punya "administrator", "manager", "staff", "read-only" default.
Tenant bisa memakai apa adanya, menyalin lalu memodifikasi, atau membuat dari nol.
System role tidak bisa dihapus tetapi bisa "di-clone" jadi custom role.

Manfaat pendekatan ini: fleksibilitas tinggi untuk berbagai struktur organisasi
(nilai jual untuk produk komersial), sambil tetap aman karena permission catalog
dikontrol aplikasi — tenant tidak bisa mengarang permission yang tidak ada.

---

## 7. Seat Licensing (Hard Limit)

Aturan inti:
- `app_subscriptions.seats_purchased` menetapkan kuota seat untuk (tenant, app).
- Jumlah `app_seats` aktif untuk (tenant, app) tidak boleh melebihi kuota.
- Memberi akses app ke user = membuat `app_seat` baru (jika kuota tersisa).
- Mencabut akses = menonaktifkan/menghapus `app_seat`; seat kembali tersedia.

Hard limit pada MVP: bila kuota penuh, permintaan menambah user ke app ditolak
dengan pesan jelas ("Seat CRM penuh: 6/6. Tambah seat untuk mengundang lebih
banyak user."). Tidak ada charge otomatis.

Penegakan harus atomik untuk mencegah race condition (dua admin menambah user
bersamaan saat tersisa 1 seat). Karena proyek memakai pendekatan no-FK dengan
validasi di application layer, penegakan kuota dilakukan dalam transaksi dengan
penguncian baris langganan (mis. SELECT ... FOR UPDATE pada baris subscription)
agar perhitungan seat konsisten.

Penghitungan lisensi: per seat per app. User yang memakai dua app menempati dua
seat (satu per app). Ini selaras dengan studi kasus tenant 1020 (11 user, 12
seat terpakai).

---

## 8. Alur Otorisasi pada Request

Setiap request ke endpoint sebuah app melewati urutan pemeriksaan:

1. Autentikasi — token valid, user aktif, milik tenant yang sesuai (identity).
2. Tenant context — set RLS (`app.current_tenant_id`) untuk isolasi data.
3. Seat check — pastikan user menempati seat aktif untuk app ini. Jika tidak,
   tolak dengan 403 "tidak punya akses ke aplikasi ini".
4. Permission check — kumpulkan permission efektif user pada app ini (gabungan
   permission dari semua role yang diberikan pada seat-nya), lalu pastikan
   permission yang dibutuhkan endpoint ada. Jika tidak, tolak 403.
5. Eksekusi — jalankan handler.

Pemeriksaan ini berlapis: gagal di langkah mana pun menghentikan request. Seat
check (lapis 2) selalu mendahului permission check (lapis 3) — tidak ada gunanya
memeriksa role bila user memang tidak berhak membuka app-nya.

Untuk performa, permission efektif user per app dapat di-cache (mis. di Redis)
dan di-invalidasi saat role/permission/seat user berubah.

---

## 9. Implementasi (FastAPI)

Contoh penegakan licensing dan permission. Kode mengikuti layering proyek
(ADR-007): pemeriksaan dipasang sebagai dependency, logika otorisasi berada di
use-case/contract, bukan tersebar.

Permission catalog & dependency:

```python
# shared/authz.py
from enum import Enum
from uuid import UUID
from fastapi import Depends, HTTPException, status

class CrmPermission(str, Enum):
    REPORTING_VIEW = "crm.reporting.view"
    REPORTING_EXPORT = "crm.reporting.export"
    DEAL_DELETE = "crm.deal.delete"
    AI_FOLLOWUP_APPROVE = "crm.ai.followup_approve"
    # ... dst

APP_CODE_CRM = "crm"


def require_app_access(app_code: str):
    """Lapis 2: pastikan user menempati seat aktif untuk app ini."""
    async def _check(
        current_user = Depends(get_current_user),
        authz = Depends(get_authz_service),   # contract, bukan service konkret
    ):
        if not await authz.has_active_seat(current_user.id, current_user.tenant_id, app_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tidak punya akses ke aplikasi '{app_code}'",
            )
        return current_user
    return _check


def require_permission(app_code: str, permission: str):
    """Lapis 3: pastikan permission ada di salah satu role user pada app ini."""
    async def _check(
        current_user = Depends(get_current_user),
        authz = Depends(get_authz_service),
    ):
        perms = await authz.effective_permissions(
            current_user.id, current_user.tenant_id, app_code
        )
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' diperlukan",
            )
        return current_user
    return _check
```

Pemakaian di router CRM (reporting):

```python
# modules/reporting/router.py
from fastapi import APIRouter, Depends
from app.shared.authz import require_app_access, require_permission, CrmPermission, APP_CODE_CRM

router = APIRouter(prefix="/reporting", tags=["reporting"])

@router.get(
    "/kpi",
    dependencies=[
        Depends(require_app_access(APP_CODE_CRM)),                      # lapis 2
        Depends(require_permission(APP_CODE_CRM, CrmPermission.REPORTING_VIEW)),  # lapis 3
    ],
)
async def get_kpi_report(...):
    # sales manager (punya crm.reporting.view) → boleh
    # sales staff (tanpa permission itu) → 403
    ...
```

Penegakan seat saat assign user (hard limit, atomik):

```python
# modules/licensing/use_case.py (konsep)
async def assign_seat(self, tenant_id, app_code, user_id):
    async with self._uow.transaction():
        sub = await self._repo.get_subscription_for_update(tenant_id, app_code)  # lock baris
        if sub is None or sub.status != "active":
            raise DomainError("Langganan app tidak aktif")

        used = await self._repo.count_active_seats(sub.id)
        if used >= sub.seats_purchased:
            raise SeatLimitReached(
                f"Seat {app_code} penuh: {used}/{sub.seats_purchased}. "
                f"Tambah seat untuk mengundang lebih banyak user."
            )

        # idempotden: satu user maksimal satu seat per app
        if await self._repo.seat_exists(sub.id, user_id):
            return  # sudah punya seat

        await self._repo.create_seat(sub.id, tenant_id, app_code, user_id)
```

Mengumpulkan permission efektif:

```python
# modules/authz/use_case.py (konsep, implement AuthzContractProtocol)
async def effective_permissions(self, user_id, tenant_id, app_code) -> set[str]:
    # (opsional) cek cache Redis dulu
    seat = await self._repo.active_seat(user_id, tenant_id, app_code)
    if not seat:
        return set()
    role_ids = await self._repo.role_ids_for_seat(seat.id)       # user_roles
    perms = await self._repo.permissions_for_roles(role_ids)     # role_permissions → permissions
    return set(perms)
```

---

## 10. Integrasi dengan Keputusan Arsitektur Lain

Selaras dengan ADR yang sudah ada:

- ADR-002 (RLS): semua tabel otorisasi tenant-scoped pakai RLS; isolasi data
  antar tenant tetap dijamin di level DB.
- ADR-004 (SSO bertahap): tabel users/apps/subscriptions/seats idealnya berada
  di domain identity yang dapat di-extract ke `pranata-shared/auth-service` pada
  Phase 2. Desain ini sudah "suite-aware" sejak awal.
- ADR-005 (no-FK): relasi antar tabel otorisasi memakai soft reference + index
  manual; penegakan integritas (mis. seat menunjuk user/sub yang valid) lewat
  write guard di use-case, dan cleanup lewat domain events (mis. saat user
  dihapus → cabut seat & user_roles-nya).
- ADR-006 (UUID v7): semua PK UUID v7.
- ADR-007 (use-case layer): otorisasi diekspos lewat `AuthzContractProtocol`
  yang diimplementasi use-case; modul lain (reporting, deals) hanya tahu contract.
- ADR-009 (reporting): endpoint reporting dilindungi `crm.reporting.view` —
  contoh konkret RBAC yang kamu minta (manager bisa, staff tidak).

---

## 11. Roadmap

Hal-hal yang sengaja ditunda dari MVP:

- Overage / soft limit: izinkan melebihi seat dengan charge otomatis per seat
  tambahan (butuh integrasi metering ke Stripe).
- Role hierarchy / inheritance: role mewarisi permission dari role lain.
- Permission berbasis kondisi (ABAC): mis. "hanya deal milik sendiri" — saat ini
  cukup lewat permission granular + filter kepemilikan di query.
- Delegated administration: admin terbatas hanya untuk app tertentu.
- Audit log perubahan role/seat (selaras dengan modul audit log di backlog).
- SSO penuh lintas app (OAuth2) saat PranataDocs hadir.

---

## 12. Edge Cases & Aturan

- User tanpa seat membuka app → 403 di lapis 2, tidak peduli role apa pun.
- Seat dicabut saat user sedang login → permission efektif jadi kosong pada
  request berikutnya; sesi tidak otomatis "memberi" akses tanpa seat. Invalidasi
  cache permission saat seat berubah.
- User dihapus dari tenant → domain event mencabut semua seat & user_roles-nya;
  seat kembali tersedia untuk dialokasikan ulang.
- Tenant menurunkan jumlah seat di bawah jumlah terpakai → kebijakan produk:
  blokir penurunan sampai seat dikurangi manual, atau tandai seat berlebih
  sebagai non-aktif berdasarkan aturan (mis. terakhir ditambahkan). MVP: blokir
  dan minta admin mencabut seat dulu (paling aman & sederhana).
- Custom role dihapus padahal masih dipakai → blokir penghapusan sampai role
  dilepas dari semua user, atau pindahkan user ke role default. MVP: blokir.
- System role tidak bisa dihapus, hanya di-clone.
- tenant_owner terakhir tidak boleh diturunkan/dihapus (selalu sisakan minimal
  satu owner) — aturan integritas level suite.

---

*Dokumen ini melengkapi paket dokumen utama PranataCRM. Pertimbangkan menambah
ADR-010 "Suite Licensing & RBAC Model" untuk meresmikan keputusan di sini.*
