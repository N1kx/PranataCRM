# PranataCRM — Frontend Technical Planning

> Rencana teknis frontend PranataCRM. Selaras dengan keputusan backend
> (modular monolith, tiga lapis otorisasi, multi-tenant) dan visi Pranata Suites.
>
> Keputusan desain (terkonfirmasi):
> - Rendering: **Hybrid** — marketing/landing SSR, app dashboard SPA-mode.
> - UI: **Component library siap pakai** (Nuxt UI / PrimeVue) demi velocity & konsistensi.
> - Struktur suite: **Satu Nuxt app per produk** (CRM sendiri, Docs sendiri) + shared package.

---

## Daftar Isi
1. Prinsip & Tujuan
2. Tech Stack Frontend
3. Strategi Rendering Hybrid
4. Struktur Folder
5. Shared Package (pranata-shared)
6. UI Component Strategy
7. State Management (Pinia)
8. Auth, Tenant & API Layer
9. Otorisasi di Frontend (3 lapis)
10. Fitur per Halaman (mapping ke backend)
11. Realtime & Async UX
12. Form, Validasi & Error Handling
13. Performance & Quality
14. Testing Strategy
15. Milestone Frontend
16. Aturan untuk AI-Generated Code

---

## 1. Prinsip & Tujuan

Frontend harus cepat dibangun (solo + AI), konsisten secara visual, dan siap
dipakai ulang lintas Pranata Suites. Tiga prinsip:

Velocity tanpa utang desain — pakai component library siap pakai, jangan bikin
design system dari nol untuk MVP. Konsistensi lintas app — komponen, tema, auth,
dan tipe data yang dipakai bersama hidup di shared package. Pemisahan zona jelas
— halaman publik (SEO) dirender server, app di balik login berjalan sebagai SPA
agar interaktif dan ringan di server.

## 2. Tech Stack Frontend

| Aspek | Pilihan | Catatan |
|---|---|---|
| Framework | Nuxt 3 (Vue 3, Vite) | hybrid rendering via routeRules |
| Styling | Tailwind CSS | utility-first, selaras component library |
| UI Library | Nuxt UI (atau PrimeVue) | siap pakai; final pilih saat spike kecil |
| State | Pinia | store modular per domain |
| Data fetching | `$fetch`/`useFetch` + composables | wrapper api client di shared |
| Auth | httpOnly cookie + refresh rotation | selaras backend |
| Form & validasi | Zod + vee-validate (atau bawaan lib) | schema reusable |
| Charts | Chart.js / unovis | dashboard & reporting |
| Tables | TanStack Table (headless) | data grid kontak/deal |
| Drag & drop | vuedraggable / native | kanban pipeline |
| i18n | @nuxtjs/i18n | dukungan bahasa lokal (nilai jual) |
| Icon | library bawaan UI / Tabler | konsisten |
| Lint/format | ESLint + Prettier | CI gate |
| Test | Vitest + Vue Test Utils, Playwright | unit + e2e |
| Deploy | Vercel | wildcard *.pranata.app |

Catatan pemilihan UI library: lakukan spike singkat (½ hari) membandingkan
Nuxt UI vs PrimeVue pada satu layar nyata (tabel kontak + form). Nuxt UI lebih
menyatu dengan ekosistem Nuxt & Tailwind; PrimeVue lebih kaya komponen kompleks
(data table, tree). Pilih satu lalu konsisten — jangan campur dua library.

## 3. Strategi Rendering Hybrid

Satu Nuxt app, dua zona rendering diatur lewat `routeRules` di `nuxt.config.ts`:

```ts
export default defineNuxtConfig({
  routeRules: {
    // Zona SSR / prerender — halaman publik, SEO penting
    '/':           { prerender: true },
    '/pricing':    { prerender: true },
    '/about':      { prerender: true },
    '/blog/**':    { isr: 3600 },          // incremental static regeneration
    // Zona SPA — app di balik login, SEO tidak perlu
    '/app/**':     { ssr: false },         // client-only, hindari beban server
    // Auth pages — ringan, boleh SSR
    '/login':      { ssr: true },
    '/register':   { ssr: true },
  },
})
```

Prinsipnya: segala sesuatu di bawah `/app/**` adalah SPA (ssr: false) — ini
dashboard, kanban, daftar kontak, panel AI. Halaman marketing dan auth dirender
server atau di-prerender agar cepat dan ramah SEO. Pemisahan ini juga menekan
biaya server (zona SPA tidak membebani Node runtime).

Konsekuensi yang harus diperhatikan: di zona SPA, tidak ada akses request server
saat render awal — semua data diambil client-side setelah mount. Tenant context
(subdomain) diresolusi di client untuk zona ini; untuk zona SSR, subdomain bisa
diresolusi di server middleware.

## 4. Struktur Folder

```
pranata-crm-frontend/
├── nuxt.config.ts            # routeRules, modules, runtime config
├── app.vue
├── assets/css/
├── layouts/
│   ├── marketing.vue         # untuk zona SSR publik
│   ├── auth.vue              # login/register
│   └── app.vue               # shell dashboard (sidebar + topbar)
├── pages/
│   ├── index.vue             # landing (SSR)
│   ├── pricing.vue           # (SSR)
│   ├── login.vue
│   ├── register.vue
│   └── app/                  # semua SPA
│       ├── index.vue         # dashboard
│       ├── contacts/
│       │   ├── index.vue
│       │   └── [id].vue
│       ├── companies/
│       ├── deals/
│       │   ├── index.vue     # kanban
│       │   └── [id].vue
│       ├── activities/
│       ├── reporting/        # dilindungi permission crm.reporting.view
│       ├── ai/
│       │   ├── followup.vue  # approval HITL
│       │   └── insights.vue
│       └── settings/
│           ├── team.vue      # kelola user & seat
│           ├── roles.vue     # custom role builder
│           └── billing.vue
├── components/
│   ├── crm/                  # KanbanBoard, ContactTable, DealScoreBadge, ...
│   ├── ai/                   # FollowUpApproval, ChatWidget, SummaryPanel
│   ├── reporting/            # KpiCard, charts
│   └── common/               # wrapper UI app-specific
├── composables/
│   ├── useContacts.ts
│   ├── useDeals.ts
│   ├── useReporting.ts
│   └── useAiAgents.ts
├── stores/                   # Pinia: auth, tenant, ui, + domain stores
├── middleware/
│   ├── auth.ts               # guard route /app/**
│   ├── tenant.ts             # resolve subdomain
│   └── app-access.ts         # cek seat (lapis 2)
├── plugins/
│   └── api.client.ts         # $fetch instance + auto refresh
└── types/                    # re-export dari shared
```

## 5. Shared Package (pranata-shared)

Karena tiap produk = satu Nuxt app, hal yang dipakai bersama tinggal di package
npm internal `@pranata/shared` (di repo `pranata-shared`). Isi:

- UI kit & tema — wrapper tipis di atas component library + design token
  (warna brand Pranata, spacing, tipografi) agar CRM & Docs konsisten.
- Auth & SSO client — composables (`useAuth`, `useSession`), api client dengan
  refresh token rotation, guard.
- Types & DTO — tipe TypeScript yang mirror DTO backend (Contact, Deal, dst) +
  tipe authz (permission code, role).
- Authz helpers — util cek permission/seat di sisi client (lihat bagian 9).
- Utils — formatter tanggal/mata uang (penting untuk i18n pasar lokal), helper umum.

Strategi versi: di tahap awal, `@pranata/shared` bisa di-link via pnpm workspace
agar iterasi cepat; saat stabil, publish sebagai versioned package. Ini selaras
dengan ADR-004 (SSO bertahap) — auth client di shared memudahkan migrasi ke SSO
penuh nanti.

## 6. UI Component Strategy

Pakai component library siap pakai sebagai fondasi, bungkus tipis untuk
kebutuhan app. Aturan:

Jangan pakai komponen library mentah langsung di halaman — bungkus dalam
komponen app/shared (mis. `<PButton>` → `<AppButton>`) agar bila suatu saat ganti
library, perubahan terlokalisasi. Komponen kompleks khusus CRM (KanbanBoard,
ContactTable, DealScoreBadge, FollowUpApproval) dibangun di atas primitives
library. Tema dan token warna diatur terpusat di shared agar brand konsisten
lintas suite.

Komponen yang akan banyak dipakai: data table (kontak, deal, activity), modal/
drawer (detail & form), form controls, toast/notification, badge/tag (status,
AI score), tabs, command palette (opsional, UX bagus), date picker, dan chart
wrapper untuk dashboard/reporting.

## 7. State Management (Pinia)

Store dipecah per domain, selaras modul backend:

```
stores/
  auth.ts        # user, suite role, session
  tenant.ts      # tenant aktif, subdomain, plan
  ui.ts          # sidebar, theme, modal state
  contacts.ts    # cache & aksi kontak
  deals.ts       # pipeline state, optimistic stage move
  reporting.ts   # KPI snapshot cache
  ai.ts          # task AI, antrian approval
  authz.ts       # permission efektif user untuk app ini (lapis 3)
```

Pola: store memegang state + aksi yang memanggil composable/api; komponen
membaca via getter. Untuk pipeline kanban, gunakan optimistic update (pindah
kartu langsung di UI, rollback bila API gagal) agar terasa responsif.

Hindari over-caching: data yang sering berubah (pipeline, activity) sebaiknya
re-fetch saat masuk halaman; data stabil (daftar role, katalog permission) boleh
di-cache lebih lama.

## 8. Auth, Tenant & API Layer

**Auth.** Login menukar kredensial dengan access token (httpOnly cookie) +
refresh token rotation, selaras backend. Api client otomatis me-refresh saat
401, lalu mengulang request. Logout mencabut token.

**Tenant resolution.** Subdomain `acme.pranata.app` menentukan tenant. Untuk
zona SSR, resolusi di server middleware; untuk zona SPA, resolusi di client saat
init. Tenant aktif disimpan di store dan dikirim sebagai konteks (backend tetap
menegakkan via RLS — frontend hanya untuk UX).

**API client.** Satu instance `$fetch` terbungkus di shared: base URL dari
runtime config, kirim cookie, tangani refresh, normalisasi error jadi bentuk
konsisten, dan sisipkan header yang diperlukan. Composable per domain memanggil
client ini, bukan `$fetch` mentah.

```ts
// composables/useDeals.ts (konsep)
export function useDeals() {
  const api = useApiClient()           // dari @pranata/shared
  const store = useDealsStore()

  async function fetchPipeline() {
    store.setLoading(true)
    try {
      store.deals = await api.get('/deals', { query: { view: 'pipeline' } })
    } finally { store.setLoading(false) }
  }

  async function moveStage(dealId: string, stage: string) {
    const prev = store.optimisticMove(dealId, stage)   // update UI dulu
    try {
      await api.patch(`/deals/${dealId}/stage`, { stage })
    } catch (e) {
      store.rollbackMove(dealId, prev)                 // rollback bila gagal
      throw e
    }
  }

  return { fetchPipeline, moveStage }
}
```

## 9. Otorisasi di Frontend (3 Lapis)

Frontend mencerminkan tiga lapis otorisasi backend untuk UX yang benar —
tapi penegakan sesungguhnya tetap di backend. Frontend hanya menyembunyikan/
menonaktifkan UI yang tidak relevan, bukan jaminan keamanan.

Lapis 1 (suite identity): setelah login, ambil profil user + suite role; simpan
di `auth` store. Menentukan akses menu level organisasi (billing, kelola user).

Lapis 2 (seat/app access): middleware `app-access.ts` memastikan user punya seat
aktif untuk CRM sebelum masuk `/app/**`; jika tidak, arahkan ke halaman "tidak
punya akses ke aplikasi ini / hubungi admin".

Lapis 3 (permission): ambil permission efektif user untuk CRM, simpan di `authz`
store. Sediakan helper untuk menyembunyikan elemen UI.

```ts
// composables/usePermission.ts (konsep, dari shared)
export function usePermission() {
  const authz = useAuthzStore()
  const can = (perm: string) => authz.permissions.has(perm)
  return { can }
}
```

```vue
<!-- contoh: menu Reporting hanya untuk yang punya permission -->
<script setup>
const { can } = usePermission()
</script>
<template>
  <NavItem v-if="can('crm.reporting.view')" to="/app/reporting">
    Reporting & KPI
  </NavItem>
</template>
```

Penting: sembunyikan menu Reporting untuk sales staff (tanpa
`crm.reporting.view`), tapi tetap andalkan backend menolak akses langsung ke
endpoint/route. Frontend = UX, backend = keamanan.

Halaman pengaturan role (`/app/settings/roles.vue`) adalah custom role builder:
menampilkan katalog permission per app dan membiarkan admin menyusun role —
mengonsumsi endpoint authz yang sama.

## 10. Fitur per Halaman (Mapping ke Backend)

| Halaman | Modul backend | Catatan UX |
|---|---|---|
| /app (dashboard) | dashboard | metric cards, chart ringkas |
| /app/contacts | contacts | tabel + filter + detail drawer |
| /app/contacts/[id] | contacts, activities | timeline aktivitas, summary AI |
| /app/companies | companies | tabel + detail |
| /app/deals | deals | kanban drag-drop, badge AI score |
| /app/deals/[id] | deals, activities | detail + riwayat + scoring |
| /app/reporting | reporting | KPI 4 kategori; dilindungi permission |
| /app/ai/followup | ai (followup) | antrian approval HITL (approve/edit/reject) |
| /app/ai/insights | ai (summarizer/scorer) | ringkasan & saran next action |
| (widget) chatbot | ai (RAG) | floating chat, jawab dari knowledge base |
| /app/settings/team | licensing, users | kelola user & alokasi seat (hard limit) |
| /app/settings/roles | authz | custom role builder + permission catalog |
| /app/settings/billing | billing | plan, Stripe portal, jumlah seat |

## 11. Realtime & Async UX

Banyak aksi AI bersifat async (scoring, draft follow-up) — diproses worker via
RabbitMQ. Frontend perlu pola untuk ini:

Untuk tugas yang dipicu user (mis. "score deal ini"): tampilkan state pending,
lalu poll status task atau terima update. Untuk MVP, polling sederhana atas
`ai_tasks` cukup; SSE/WebSocket bisa menyusul. Antrian approval follow-up
menampilkan daftar draft berstatus `awaiting_approval` dengan aksi approve/edit/
reject; setelah aksi, refresh daftar.

Aktivitas baru (timeline) bisa memakai polling ringan atau refetch saat fokus.
Hindari over-engineering realtime di MVP; tambahkan WebSocket hanya bila UX
benar-benar menuntut.

## 12. Form, Validasi & Error Handling

Definisikan schema validasi (Zod) yang reusable — idealnya sebagian tipe diturunkan
dari DTO di shared agar selaras dengan backend. Form pakai vee-validate atau
mekanisme bawaan UI library; tampilkan error per-field dan error global.

Normalisasi error API jadi bentuk konsisten di api client (kode, pesan, detail
field) sehingga komponen bisa menampilkan pesan ramah. Tangani kasus umum: 401
(refresh/relogin), 403 (tampilkan "tidak diizinkan" — selaras lapis 2/3), 409
(konflik, mis. seat penuh → ajak upgrade), 422 (validasi).

## 13. Performance & Quality

Zona SPA: code splitting per route otomatis (Nuxt). Lazy-load komponen berat
(chart, kanban) dan widget chatbot. Zona SSR: prerender halaman statis, ISR untuk
blog. Optimasi gambar via modul Nuxt Image. Pantau bundle size sebagai CI gate.

Aksesibilitas: andalkan komponen library yang sudah a11y-aware, jaga kontras dan
fokus keyboard. i18n sejak awal (string tidak hardcode) — mendukung pasar lokal
yang jadi target bisnis.

## 14. Testing Strategy

| Level | Tool | Cakupan |
|---|---|---|
| Unit | Vitest + Vue Test Utils | composables, util, store, komponen kecil |
| Component | Vitest + Testing Library | komponen kunci (KanbanCard, FollowUpApproval) |
| E2E | Playwright | alur kritikal: login, buat kontak, pindah stage, approve follow-up, akses reporting per role |
| Visual (opsional) | Playwright snapshot | regresi tampilan komponen utama |

Fokuskan e2e pada alur yang mengikat banyak lapis: mis. "login sebagai sales
staff → menu Reporting tidak muncul → akses /app/reporting langsung ditolak".
Ini sekaligus memverifikasi integrasi otorisasi 3 lapis.

## 15. Milestone Frontend (selaras 9 minggu)

| Minggu | Fokus frontend |
|---|---|
| 1 | Setup Nuxt, routeRules, shared package link, layout shell, auth pages |
| 2 | Tenant resolution, api client + refresh, store auth/tenant, guard |
| 3 | Contacts: tabel, filter, detail drawer; companies |
| 4 | Activities timeline; mulai deals list |
| 5 | Kanban pipeline (drag-drop, optimistic), dashboard + charts |
| 6 | AI score badge, panel insights; integrasi async/polling |
| 7 | Follow-up approval (HITL), summary panel, chatbot widget |
| 8 | Reporting & KPI (dengan permission guard), settings: team/seat, billing |
| 9 | Custom role builder, polish, e2e tests, a11y & i18n pass, deploy |

Catatan: settings roles (custom role builder) cukup kompleks — bila waktu mepet,
versi MVP cukup memilih dari system roles dulu, builder penuh menyusul.

## 16. Aturan untuk AI-Generated Code (masukkan ke CLAUDE.md / .cursorrules)

1. Jangan pakai komponen UI library mentah di halaman — selalu lewat wrapper
   app/shared agar mudah diganti.
2. Data fetching lewat composable + api client shared, bukan `$fetch` mentah.
3. Zona `/app/**` selalu `ssr: false`; jangan andalkan context server di sana.
4. Cek permission untuk elemen UI sensitif via `usePermission().can(...)`, tapi
   ingat backend tetap penjaga sebenarnya.
5. Tipe data (DTO) di-import dari `@pranata/shared`, jangan duplikasi tipe.
6. Tampilkan state loading/empty/error untuk setiap data fetch.
7. Pipeline & aksi cepat pakai optimistic update + rollback.
8. String UI tidak hardcode — lewat i18n.
9. Store dipecah per domain; jangan satu store raksasa.
10. Komponen kompleks (kanban, approval) punya unit/component test.

---

*Dokumen ini melengkapi paket dokumen PranataCRM. Selaras dengan ADR-002 (RLS),
ADR-004 (SSO bertahap), ADR-007 (use-case/contract), ADR-009 (reporting), dan
ADR-010 (licensing & RBAC). Pertimbangkan ADR-011 "Frontend Rendering & Suite
Structure" untuk meresmikan keputusan hybrid rendering + satu app per produk.*
