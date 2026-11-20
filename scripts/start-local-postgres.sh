#!/usr/bin/env bash
# Project-local PostgreSQL cluster on port 55432. Mirrors scripts/start-local-postgres.ps1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/.data/postgres"
PORT=55432
PG_BIN="${PG_BIN:-}"

if [[ -z "$PG_BIN" ]]; then
  for candidate in /usr/lib/postgresql/*/bin; do
    if [[ -x "$candidate/initdb" ]]; then
      PG_BIN="$candidate"
    fi
  done
fi

if [[ ! -x "$PG_BIN/initdb" ]]; then
  echo "PostgreSQL initdb was not found. Set PG_BIN to the server bin directory." >&2
  exit 1
fi

mkdir -p "$DATA"

if [[ ! -f "$DATA/PG_VERSION" ]]; then
  "$PG_BIN/initdb" -D "$DATA" -U bizpilot --auth-local=trust --auth-host=trust --encoding=UTF8 --locale=C
  cat >> "$DATA/postgresql.conf" <<EOF

listen_addresses = '127.0.0.1'
port = $PORT
unix_socket_directories = '/tmp'
EOF
fi

if ! "$PG_BIN/pg_ctl" -D "$DATA" status >/dev/null 2>&1; then
  "$PG_BIN/pg_ctl" -D "$DATA" -l "$DATA/postgres.log" start
fi

"$PG_BIN/pg_isready" -h 127.0.0.1 -p "$PORT" -U bizpilot >/dev/null

exists="$("$PG_BIN/psql" -h 127.0.0.1 -p "$PORT" -U bizpilot -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='bizpilot'")"
if [[ "$exists" != "1" ]]; then
  "$PG_BIN/createdb" -h 127.0.0.1 -p "$PORT" -U bizpilot bizpilot
fi

echo "PostgreSQL ready on 127.0.0.1:$PORT database bizpilot"
