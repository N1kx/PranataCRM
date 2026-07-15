# ADR-003: Human-in-the-Loop untuk Follow-up Agent

**Status:** Accepted
**Date:** 2025-XX-XX

## Context
Follow-up Agent mengirim email atas nama user ke prospek. Email yang salah
konten/timing bisa merusak hubungan dan reputasi domain pengirim.

## Decision
Terapkan Human-in-the-Loop: agent membuat draft (status `awaiting_approval`),
user me-review, lalu Approve / Edit+Approve / Reject. Email hanya terkirim
setelah approve.

## Benefit
- Nol risiko email otomatis yang tidak pantas terkirim.
- User tetap memegang kendali; membangun kepercayaan pada AI secara bertahap.
- Pola UX yang baik dan menarik untuk didemokan ke pembeli/recruiter.

## Trade-off
- Tidak fully automated (memang disengaja) — ada langkah manual.
- Perlu membangun UI approval queue dan state machine tambahan.
- Ada jeda antara trigger dan pengiriman.

## Future Consideration
Setelah terkumpul cukup riwayat "approved tanpa edit", bisa ditambah mode
auto-send untuk segmen/kontak tertentu dengan trust score tinggi.

## Alternatives Considered
- Fully automated send — ditolak: risiko reputasi & hubungan terlalu tinggi.
- Tanpa agent (manual penuh) — kehilangan nilai automasi.
