# Runbook — PostgreSQL Migration (S2-1)

Sprint 2 sonu itibariyle FinPilot **PostgreSQL-ready** durumda. Tam aktivasyon Sprint 3'te `auth/database.py` async-SQLAlchemy refactor'ü ile gelecek.

## Mevcut Durum

| Bileşen | Durum |
|---------|-------|
| Migration 001 | ✅ Dialect-aware (SQLite + PostgreSQL) |
| `migrations/env.py` | ✅ `DATABASE_URL` env okur |
| docker-compose `postgres` | ✅ `db` profile (opt-in) |
| `requirements.txt` | ✅ sqlalchemy + alembic + psycopg2 + asyncpg |
| `auth/database.py` | ⚠️ Halen `sqlite3` stdlib — Sprint 3'te async SA'ya taşınacak |

## Postgres'i Lokalde Ayağa Kaldır

```bash
docker compose --profile db up -d postgres
docker exec -it finpilot_postgres psql -U finpilot -d finpilot -c "\dt"
```

## Alembic'i Postgres'e Yönelt

```bash
export DATABASE_URL="postgresql://finpilot:finpilot_dev_2026@localhost:5432/finpilot"
alembic upgrade head
```

`migrations/versions/001_initial_schema.py`, dialect tespit ederek otomatik olarak:
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `INTEGER GENERATED ALWAYS AS IDENTITY`
- `INTEGER DEFAULT 0/1` (bool) → `BOOLEAN`
- `TEXT NOT NULL` (timestamp) → `TIMESTAMPTZ`
- `REAL` → `DOUBLE PRECISION`

## Production Geçiş Adımları (Sprint 3'te tamamlanacak)

1. `auth/database.py` → SQLAlchemy 2.0 async session factory
2. `Database()` çağrılarını `async with get_session()` ile değiştir
3. Veri taşıma scripti: `scripts/migrate_sqlite_to_pg.py` (SELECT → INSERT)
4. Smoke test: `pytest tests/test_db_postgres.py`
5. `DATABASE_URL` env'i `.env` ve `docker-compose.yml` api environment'a aç
6. `db` profile'ı default'a yükselt (profiles bloğunu sil)

## Rollback

DATABASE_URL'i unset et veya `sqlite:///data/finpilot.db` olarak ayarla. Migration 001 her iki dialekti de destekler.

## İlgili Alarmlar

`monitoring/alerts.yml` → şu an PostgreSQL-spesifik alert yok. Sprint 3 sonrası:
- `pg_up == 0` → `PostgresDown` (critical)
- `pg_stat_activity_count > 80` → `PostgresHighConnections` (warning)
