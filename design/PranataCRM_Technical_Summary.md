# PranataCRM — Technical Summary & Architecture Decisions

> Dokumen referensi teknis lengkap. Setiap keputusan arsitektur disertai
> benefit dan trade-off. Disusun sebagai basis technical planning dan sebagai
> lampiran teknis proposal bisnis.
>
> Status: Living document. Versi ini mencakup keputusan hingga sesi terakhir,
> termasuk RabbitMQ sebagai message broker dan modul Reporting & KPI.

---

## Daftar Isi
1. Identitas & Visi Project
2. Ringkasan Keputusan Arsitektur (dengan Benefit & Trade-off)
3. Tech Stack
4. Modul & Fitur (termasuk Reporting & KPI)
5. Diagram Arsitektur
6. Database Schema
7. Daftar ADR
8. Milestone
9. Persiapan Sebelum Coding
10. Catatan untuk Komersialisasi

---

## 1. Identitas & Visi Project

| Atribut | Nilai |
|---|---|
| Nama | PranataCRM |
| Tipe | Multi-tenant AI-powered CRM Platform |
| Konteks | Bagian dari Pranata Suites (CRM pertama, DMS menyusul) |
| Tujuan | Portfolio Senior Full Stack **dan** kandidat produk komersial |
| Pengerjaan | Solo, dibantu AI untuk coding & QA |
| Estimasi | Paruh waktu 2–3 jam/hari, ~9 minggu untuk MVP |
| Domain | `pranata.app` (subdomain per tenant: `acme.pranata.app`) |

Visi Pranata Suites: kumpulan aplikasi yang masing-masing berdiri sendiri
namun terhubung via SSO/shared auth. CRM dan DMS akan disatukan ke dalam suite.
Arsitektur CRM dirancang sejak awal agar mudah diintegrasikan ke suite dan
dipisah ke microservice bila diperlukan.

---

## 2. Ringkasan Keputusan Arsitektur (Benefit & Trade-off)

### 2.1 Modular Monolith
**Keputusan:** Satu deployable, modul loosely coupled, tiap modul layered.
Antar modul berinteraksi via contract (Protocol), bukan import langsung.

**Benefit:**
- Sederhana untuk dikembangkan & dideploy solo (vs microservice penuh).
- Batas modul jelas → kode terorganisir, mudah dipahami AI saat generate.
- Siap dipisah ke microservice tanpa rombak besar.

**Trade-off:**
- Disiplin batas modul harus dijaga manual (mudah "bocor" jika lengah).
- Satu proses → scaling masih monolitik sampai benar-benar dipisah.
- Boilerplate antar-layer lebih banyak daripada pendekatan langsung.

### 2.2 Contract di UseCase Layer (service internal murni)
**Keputusan:** Layering router → use_case → service → repository → model.
Contract (Protocol) diimplementasi oleh use_case; service tidak pernah diakses
dari luar modulnya.

**Benefit:**
- Batas modul sangat tegas; service tidak mungkin di-couple dari luar.
- Use-case jadi titik orkestrasi & konversi DTO yang jelas.
- Migrasi microservice mulus: ganti implementasi Protocol di container.py.

**Trade-off:**
- Satu layer tambahan → lebih banyak boilerplate.
- Risiko use-case "anemic" jika logic menumpuk di service.
- Untuk operasi trivial, use-case bisa terasa tipis.

### 2.3 UUID v7 sebagai Primary Key (application-generated)
**Keputusan:** Semua PK UUID v7, di-generate di Python (kompatibel PostgreSQL ≤15).

**Benefit:**
- Sequential → performa index/write mendekati BIGINT.
- Tidak enumerable → aman dari IDOR, cocok multi-tenant.
- Bisa dibuat tanpa round-trip DB → siap distribusi/microservice.
- Portabel (tidak butuh `uuidv7()` DB yang baru ada di PostgreSQL 18).

**Trade-off:**
- 16 byte vs 8 byte BIGINT (dampak kecil pada skala ini).
- Timestamp sedikit membocorkan waktu pembuatan record.
- Bergantung jam sistem benar (perlu NTP).

### 2.4 Tanpa Foreign Key (Soft Reference + 3 Pilar)
**Keputusan:** Tidak ada FK constraint sama sekali. Integrity dijaga aplikasi
via write guard, delete cascade (domain events), dan orphan sweeper.

**Benefit:**
- Konsisten dengan prinsip "interaksi via contract".
- Boundary modul bisa berubah tanpa migrasi drop-constraint berisiko.
- Tabel high-volume (activities, ai_tasks) bebas dipartisi/shard.
- Write lebih cepat tanpa constraint check.

**Trade-off:**
- DB tidak lagi menjamin integrity → wajib bangun 3 pilar.
- Cleanup jadi tanggung jawab aplikasi (rawan lupa tanpa disiplin).
- Index WAJIB dibuat manual untuk tiap kolom referensi.
- Butuh orphan sweeper sebagai jaring pengaman.

### 2.5 PostgreSQL RLS untuk Tenant Isolation
**Benefit:** Isolasi dijamin di level DB; mencegah kebocoran lintas tenant
akibat bug aplikasi; nilai jual keamanan untuk enterprise.
**Trade-off:** Set session variable tiap koneksi; migrasi & testing lebih
kompleks; sedikit overhead performa.

### 2.6 LiteLLM (LLM Abstraction)
**Benefit:** Satu API untuk semua provider; ganti provider via env variable;
zero vendor lock-in.
**Trade-off:** Satu dependency & lapis abstraksi tambahan; bergantung stabilitas
API LiteLLM.

### 2.7 Human-in-the-Loop (Follow-up Agent)
**Benefit:** Nol risiko email otomatis tak pantas; user pegang kendali; UX bagus
untuk demo.
**Trade-off:** Tidak fully automated; perlu UI approval queue; ada jeda kirim.

### 2.8 RabbitMQ sebagai Message Broker (BARU)
**Keputusan:** RabbitMQ untuk Celery broker. Redis tetap untuk cache, session,
rate limiting.

**Benefit:**
- Jaminan pengiriman kuat (persistent queue, ack, publisher confirms).
- Routing canggih (exchange, DLQ, priority) → pisah email/AI/webhook.
- Retry & dead-letter matang; visibilitas via management UI.
- Lebih cocok untuk beban kritikal produk komersial.

**Trade-off:**
- Operasional lebih berat dari Redis (komponen tambahan, memori/CPU).
- Kurva belajar lebih curam (exchange, binding, routing key).
- Untuk beban ringan, Redis broker lebih sederhana.
- Free tier hosting mungkin perlu self-host atau plan berbayar.

### 2.9 Modul Reporting & KPI (BARU)
**Keputusan:** Modul read-only tersendiri, akses data via contract, agregasi
berat via job terjadwal ke tabel snapshot.

**Benefit:** Insight nyata untuk manajer; diferensiasi (KPI AI effectiveness);
performa terjaga via snapshot.
**Trade-off:** Modul & tabel tambahan; job agregasi perlu dipantau; snapshot
bisa basi antar interval.

---

## 3. Tech Stack

| Layer | Technology | Catatan |
|---|---|---|
| Backend | FastAPI (Python) + SQLAlchemy async + Alembic | |
| Frontend | Nuxt 3 + Tailwind + Pinia | |
| Database | PostgreSQL 15 + pgvector | UUID v7, no FK, RLS |
| Cache | Redis | session, rate limit, cache |
| **Queue (broker)** | **RabbitMQ** | **menggantikan Redis sbg broker** |
| Worker | Celery + Celery beat | email, webhook, AI, agregasi report |
| Auth | JWT + httpOnly cookie + refresh rotation | |
| Email | Resend (free 3k/bulan) | |
| AI Abstraction | LiteLLM | zero vendor lock-in |
| LLM Dev | Ollama (llama3.1:8b) | lokal, gratis, offline |
| LLM Prod | Groq (llama-3.1-8b-instant) | free 14.4k req/hari |
| LLM Fallback | OpenRouter (mistral-7b) | backup |
| Deploy FE | Vercel | free tier |
| Deploy BE | Railway | free tier (RabbitMQ via container/CloudAMQP) |

---

## 4. Modul & Fitur

### Core Layer
Contacts & Companies, Deals (pipeline Kanban), Activities (timeline),
Dashboard, Auth & RBAC (owner/admin/member), Billing (Stripe + webhook).

### AI Agent Layer (4 agents)
Follow-up Agent (HITL), Deal Scorer (8 signals + LLM), Conversation Summarizer,
RAG Chatbot (pgvector).

### Reporting & KPI Layer (BARU — di luar dashboard)
1. **Sales performance** — revenue, win rate, average deal size, sales cycle
   length, leaderboard per rep.
2. **Activity & productivity** — activities per user, response time ke lead,
   task completion rate, email open/click rate.
3. **Pipeline health** — conversion per stage, stage duration (bottleneck),
   weighted forecast, stale & at-risk deals.
4. **AI effectiveness** — akurasi deal scorer, follow-up approval & conversion,
   LLM cost/token per tenant, chatbot deflection rate.

Output: report dengan filter (periode/owner/tim) + ekspor CSV/Excel. Agregasi
berat via Celery beat ke tabel `report_snapshots`.

### Modul Tambahan (Backlog, urut prioritas)
- Engagement (★★★): email sequences, tasks & reminders, lead capture forms,
  meeting scheduler.
- Intelligence (★★): lead scoring, churn prediction, email intelligence.
- Platform (★): integrations (Slack/WhatsApp), public API, custom fields,
  audit log.

---

## 5. Diagram Arsitektur

Lihat berkas `pranataCRM_architecture.svg` (disertakan dalam paket dokumen).
Lapisan: Client → FastAPI Middleware → Modular Monolith → (Data Stores +
Queue & Workers) → External Services + LLM Layer.

---

## 6. Database Schema (Ringkasan)

Semua tabel: PK UUID v7, kolom referensi = soft reference (UUID, no FK),
tenant-scoped tables pakai RLS, index manual untuk tiap kolom referensi.

| Tabel | Modul | Catatan |
|---|---|---|
| tenants | auth | slug unik (subdomain), plan, stripe fields |
| users | auth | role owner/admin/member |
| refresh_tokens | auth | rotation, revocation |
| contacts | crm | status, custom_fields JSONB |
| companies | crm | industry, size, arr |
| deals | crm | stage, value, ai_score + signals + reasoning |
| activities | crm | high-volume, kandidat partisi |
| ai_tasks | ai | agent_type, status, input/output |
| knowledge_base | ai | embedding vector(1536), pgvector |
| webhooks | billing | event_type, payload, retry_count |
| report_snapshots | reporting | report_type, period, payload JSONB |

---

## 7. Daftar ADR

| ADR | Judul | Status |
|---|---|---|
| 001 | LiteLLM sebagai LLM Abstraction Layer | Accepted |
| 002 | PostgreSQL RLS untuk Tenant Isolation | Accepted |
| 003 | Human-in-the-loop untuk Follow-up Agent | Accepted |
| 004 | SSO Strategy untuk Pranata Suites (bertahap) | Partially Accepted |
| 005 | Tanpa Foreign Key (Soft Reference + 3 pilar) | Accepted |
| 006 | UUID v7 sebagai Primary Key (app-generated, ≤PG15) | Accepted |
| 007 | Modular Monolith + Contract di UseCase Layer | Accepted |
| 008 | RabbitMQ sebagai Message Broker | Accepted |
| 009 | Modul Reporting & KPI (Operational Analytics) | Accepted |

Dokumen lengkap tiap ADR ada di folder `adr/`.

---

## 8. Milestone (9 Minggu — MVP)

| Minggu | Fokus |
|---|---|
| 1 | Foundation & Auth (JWT, tenant middleware, RLS) |
| 2 | CRM Core (contacts, companies, RBAC) |
| 3 | Deal Pipeline + Dashboard stats |
| 4 | Frontend Base (Nuxt 3, auth flow, contacts) |
| 5 | Frontend Pipeline + Dashboard (Kanban, charts) |
| 6 | LiteLLM Orchestrator + Deal Scorer |
| 7 | Follow-up Agent (HITL) + Summarizer |
| 8 | RAG Chatbot + Stripe + Reporting dasar |
| 9 | Polish, Testing, Deploy |

> Reporting lanjutan, engagement, dan intelligence layer = backlog post-MVP.

---

## 9. Persiapan Sebelum Coding

1. File instruksi AI (`CLAUDE.md` / `.cursorrules`) berisi aturan:
   modular (import via contract, DTO crossing, wiring di container),
   no-FK (write guard, publish event, subscribe, index, sweeper),
   layering (contract di use_case, service internal), UUID v7.
2. Skeleton repo + `container.py` + `shared/` (contracts, events, integrity, types).
3. docker-compose (Postgres, Redis, RabbitMQ, backend, worker, beat, frontend).
4. Makefile (`make bootstrap`).
5. Template satu modul lengkap (mis. contacts) sesuai ADR 005–007 sebagai
   referensi untuk AI tiru.

---

## 10. Catatan untuk Komersialisasi

Karena PranataCRM berpotensi dijual, beberapa keputusan teknis sudah selaras
dengan kebutuhan produk:
- RLS + no-FK + RBAC → keamanan & isolasi data (nilai jual enterprise).
- LiteLLM → zero vendor lock-in (mengurangi risiko biaya AI).
- RabbitMQ → keandalan pemrosesan job (penting untuk SLA).
- Reporting & KPI + AI effectiveness → diferensiasi dari CRM komoditas.
- Modular monolith → biaya operasi rendah di awal, jalur scaling jelas.

Detail aspek bisnis (pasar, pricing, GTM, finansial) ada di dokumen terpisah:
`PranataCRM_Business_Proposal.md`.
