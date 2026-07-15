# ADR-007: Modular Monolith dengan Contract Diimplementasi di UseCase Layer

**Status:** Accepted
**Date:** 2025-XX-XX
**Deciders:** [Nama kamu]
**Berlaku untuk:** Struktur seluruh modul backend PranataCRM

---

## Context

PranataCRM dibangun sebagai modular monolith: satu deployable, beberapa modul
yang loosely coupled, tiap modul layered. Tujuannya agar pemisahan ke
microservice di masa depan berjalan mulus.

Antar modul tidak boleh tightly coupled. Di bahasa seperti Go/Java/C#,
contract direpresentasikan dengan `interface`. Di Python, padanannya adalah
`typing.Protocol` (structural typing, mirip Go).

Pertanyaan desain: kelas mana yang mengimplementasikan contract tersebut?
Pada praktik umum, service yang mengimplementasi contract. Namun untuk
PranataCRM diputuskan pemisahan yang lebih tegas: **contract diimplementasikan
oleh UseCase layer, dan service menjadi internal murni** — tidak pernah diakses
dari luar modulnya. Ini selaras dengan semangat Clean Architecture, di mana
use-case adalah orchestrator yang mengekspos kapabilitas modul, sementara
service/domain logic adalah detail internal.

## Decision

Setiap modul mengikuti layered architecture berikut, dari luar ke dalam:

```
router  →  use_case  →  service  →  repository  →  model
            (impl Protocol)  (internal)   (DB)
```

Peran tiap layer:

- **router.py** — adapter HTTP. Menerima request, panggil use-case, kembalikan
  response. Tidak mengandung business logic. Hanya memanggil use-case modulnya
  sendiri.

- **use_case.py** — orchestrator dan SATU-SATUNYA implementor contract
  (Protocol). Inilah pintu masuk modul dari dunia luar (router modul sendiri
  maupun modul lain). Use-case memanggil service internal, dan jika butuh
  kapabilitas modul lain, ia depend pada Protocol modul lain (bukan use-case
  konkretnya). Use-case mengubah model/internal jadi DTO saat melintasi batas.

- **service.py** — domain logic internal modul. INTERNAL MURNI: tidak pernah
  di-import atau dipanggil dari luar modulnya. Tidak mengimplementasi contract.
  Tidak tahu apa-apa tentang modul lain.

- **repository.py** — akses database untuk model milik modul.

- **models.py / schemas.py** — ORM model dan Pydantic schema internal modul.

Contract dan DTO diletakkan di `shared/contracts/`. Wiring (menghubungkan
use-case konkret ke Protocol yang dibutuhkan modul lain) HANYA terjadi di
`container.py`.

### Aturan keras (tetap berlaku dari keputusan sebelumnya)

1. Antar modul HANYA boleh import dari `shared/contracts/`. Dilarang import
   `use_case`, `service`, `repository`, atau `model` modul lain secara langsung.
2. DTO (frozen dataclass) adalah satu-satunya bentuk data yang melintasi batas
   modul. Dilarang mengoper ORM model atau Pydantic schema internal antar modul.
3. Wiring concrete class ke Protocol HANYA di `container.py`.
4. Contract diimplementasi oleh `use_case`, BUKAN `service`.
5. `service` tidak boleh diakses dari luar modulnya (internal murni).

### Struktur folder per modul

```
modules/contacts/
├── router.py            # HTTP, panggil ContactUseCase
├── use_case.py          # implement ContactContractProtocol (pintu modul)
├── service.py           # internal: domain logic contacts
├── repository.py        # DB access
├── models.py            # ORM
└── schemas.py           # Pydantic internal

shared/contracts/
├── contact_contract.py  # ContactContractProtocol + ContactDTO
└── deal_contract.py     # DealContractProtocol + DealDTO
```

### Contoh kode

Contract (di shared):

```python
# shared/contracts/contact_contract.py
from typing import Protocol, runtime_checkable
from uuid import UUID
from dataclasses import dataclass

@dataclass(frozen=True)
class ContactDTO:
    id: UUID
    tenant_id: UUID
    first_name: str
    email: str | None
    status: str

@runtime_checkable
class ContactContractProtocol(Protocol):
    async def get_by_id(self, contact_id: UUID, tenant_id: UUID) -> ContactDTO | None: ...
    async def exists(self, contact_id: UUID, tenant_id: UUID) -> bool: ...
```

Use-case sebagai implementor contract (service tetap internal):

```python
# modules/contacts/use_case.py
from uuid import UUID
from app.shared.contracts.contact_contract import ContactDTO
from app.modules.contacts.service import ContactService  # internal modul ini

class ContactUseCase:
    """
    Implement ContactContractProtocol secara struktural.
    Inilah pintu masuk modul contacts dari luar.
    Service dipakai di sini, tapi tidak pernah bocor keluar modul.
    """
    def __init__(self, service: ContactService):
        self._service = service

    async def get_by_id(self, contact_id: UUID, tenant_id: UUID) -> ContactDTO | None:
        contact = await self._service.get(contact_id, tenant_id)  # ORM model internal
        if not contact:
            return None
        return ContactDTO(                      # konversi ke DTO saat menyeberang batas
            id=contact.id,
            tenant_id=contact.tenant_id,
            first_name=contact.first_name,
            email=contact.email,
            status=contact.status,
        )

    async def exists(self, contact_id: UUID, tenant_id: UUID) -> bool:
        return await self._service.exists(contact_id, tenant_id)
```

Service internal murni (tidak implement contract, tidak tahu modul lain):

```python
# modules/contacts/service.py
class ContactService:
    def __init__(self, repo: ContactRepository):
        self._repo = repo

    async def get(self, contact_id, tenant_id):
        return await self._repo.find_by_id(contact_id, tenant_id)  # ORM model

    async def exists(self, contact_id, tenant_id) -> bool:
        return await self._repo.exists(contact_id, tenant_id)
```

Modul lain depend pada Protocol, bukan use-case konkret:

```python
# modules/deals/use_case.py
from app.shared.contracts.contact_contract import ContactContractProtocol

class DealUseCase:
    def __init__(self, service, contact: ContactContractProtocol):
        self._service = service
        self._contact = contact          # hanya tahu Protocol

    async def create_deal(self, tenant_id, contact_id, title, value):
        # validasi referensi lewat contract (lihat ADR-005 pilar 1)
        if not await self._contact.exists(contact_id, tenant_id):
            raise ValueError("contact_id tidak ditemukan")
        return await self._service.create(tenant_id, contact_id, title, value)
```

Wiring di satu tempat:

```python
# container.py — satu-satunya tempat concrete class dirakit
from fastapi import Depends
from app.shared.contracts.contact_contract import ContactContractProtocol

async def get_contact_usecase(db=Depends(get_db)) -> ContactContractProtocol:
    return ContactUseCase(ContactService(ContactRepository(db)))

async def get_deal_usecase(
    db=Depends(get_db),
    contact: ContactContractProtocol = Depends(get_contact_usecase),
):
    return DealUseCase(DealService(DealRepository(db)), contact=contact)
```

## Consequences

### Positif
- Batas modul sangat tegas: hanya use-case (via Protocol) yang terekspos;
  service benar-benar internal sehingga sulit terjadi coupling tak sengaja.
- Single responsibility lebih jelas: use-case mengorkestrasi & menyeberangkan
  DTO; service fokus domain logic tanpa peduli kontrak lintas modul.
- Testing berlapis: service ditest tanpa contract; use-case ditest terhadap
  Protocol; modul lain cukup pakai mock yang memenuhi Protocol.
- Migrasi ke microservice mulus: ganti implementasi Protocol di container.py
  dari `XUseCase` lokal menjadi `XHttpClient` — router, service, dan modul
  konsumen tidak berubah.

### Negatif (dan mitigasinya)
- Satu layer tambahan (use-case) → sedikit lebih banyak boilerplate per modul.
  Mitigasi: pola konsisten, mudah di-template, cocok untuk di-generate AI.
- Risiko use-case jadi "anemic pass-through" jika semua logic ada di service.
  Mitigasi: tempatkan orkestrasi lintas-layanan dan konversi DTO di use-case;
  domain logic tetap di service. Keduanya punya peran berbeda yang jelas.
- Untuk operasi sangat sederhana, use-case bisa terasa tipis. Diterima demi
  konsistensi batas modul.

## Aturan untuk AI-Generated Code (masukkan ke CLAUDE.md / .cursorrules)

1. Tiap modul WAJIB punya layer: router → use_case → service → repository → model.
2. Contract (Protocol) diimplementasi HANYA oleh `use_case`.
3. `service` tidak boleh di-import dari luar modulnya.
4. Antar modul hanya lewat `shared/contracts/`; oper DTO, bukan ORM model.
5. Konversi ORM↔DTO terjadi di `use_case` (titik menyeberang batas).
6. Wiring concrete → Protocol hanya di `container.py`.

## Alternatives Considered

1. **Contract diimplementasi oleh service** — ditolak: service jadi terekspos
   lintas modul, batas kurang tegas, mudah terjadi coupling tak sengaja.
2. **Tanpa use-case (router → service langsung)** — ditolak: tidak ada tempat
   netral untuk orkestrasi lintas modul & konversi DTO; service terpaksa tahu
   tentang contract modul lain.
3. **ABC alih-alih Protocol** — ditolak: ABC butuh inheritance eksplisit;
   Protocol (structural typing) lebih fleksibel dan memudahkan mock/HTTP-client
   sebagai implementor yang sama saat migrasi microservice.
