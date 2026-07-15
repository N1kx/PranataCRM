# ADR-008: RabbitMQ sebagai Message Broker (menggantikan Redis sebagai broker)

**Status:** Accepted
**Date:** 2026-06-10

## Context
PranataCRM memproses pekerjaan asinkron: pengiriman email, pemrosesan webhook
Stripe, dan tugas AI (scoring, follow-up draft, summarization). Dibutuhkan
message broker untuk Celery. Redis bisa berperan sebagai broker, namun untuk
kebutuhan yang makin serius (kemungkinan produk komersial), dipilih RabbitMQ.

Redis tetap dipakai untuk cache, session, dan rate limiting — hanya peran
"broker" yang dipindah ke RabbitMQ.

## Decision
Gunakan RabbitMQ sebagai message broker untuk Celery. Redis tetap sebagai
cache/session/rate-limit store (dan opsional sebagai result backend).

## Benefit
- Jaminan pengiriman lebih kuat: persistent queue, message acknowledgement,
  publisher confirms — pekerjaan tidak hilang saat worker/broker restart.
- Routing canggih: exchange (direct/topic/fanout), dead-letter queue untuk
  pesan gagal, priority queue — cocok untuk memisah email vs AI vs webhook.
- Retry & DLQ matang: pesan gagal bisa diarahkan ke dead-letter untuk inspeksi,
  bukan hilang diam-diam.
- Visibilitas operasional: management UI untuk memantau queue, throughput,
  consumer — berharga untuk operasi produk komersial.
- Skala lebih baik untuk beban kerja yang kompleks dan kritikal.

## Trade-off
- Operasional lebih berat dari Redis: satu komponen tambahan untuk dikelola,
  konsumsi memori/CPU lebih besar.
- Kurva belajar lebih curam (konsep exchange, binding, routing key, vhost).
- Untuk beban ringan, Redis sebagai broker lebih sederhana dan cukup.
- Di free tier hosting, RabbitMQ mungkin perlu plan berbayar atau self-host
  (mis. CloudAMQP free tier kecil, atau container di Railway).

## Catatan Implementasi
- Celery broker URL: `amqp://user:pass@host:5672/vhost`.
- Result backend boleh tetap Redis (`redis://...`) untuk kesederhanaan.
- Definisikan queue terpisah: `emails`, `webhooks`, `ai`, dengan DLQ masing-masing.
- Untuk dev lokal, jalankan RabbitMQ via Docker Compose (`rabbitmq:3-management`).

## Alternatives Considered
- Redis sebagai broker — ditolak untuk kebutuhan komersial: jaminan pengiriman
  dan routing lebih lemah, tidak ada DLQ native, visibilitas terbatas.
- Kafka — ditolak: terlalu berat untuk skala saat ini; lebih cocok untuk
  event streaming volume sangat tinggi, bukan task queue CRM.
- AWS SQS / cloud queue — ditolak untuk saat ini: menambah vendor lock-in dan
  bertentangan dengan preferensi kontrol penuh; bisa dipertimbangkan nanti.
