Rehearsal commands (read-only on live): docker exec finvest-live-db-1 pg_dump -U finvest -Fc finvest > live.dump (6.8 s, 47.6 MB);
test stack: docker compose -p finvest-test-be -f docker-compose.yml -f docker-compose.port.yml up -d db (db port 15433, 15432 is harbor-local);
restore: timescaledb_pre_restore; pg_restore --no-owner; timescaledb_post_restore (12.8 s);
alembic -c apps/api/alembic.ini upgrade head (1.8-2.0 s wall incl. container start); downgrade 0009 (1.5 s).
