#!/usr/bin/env bash
# Consistent backup of the database + all stored files. Safe to run while the app is running.
# Usage: ./scripts/backup.sh      (env: DATA_DIR, OUT_DIR, KEEP)
set -euo pipefail
DATA_DIR="${DATA_DIR:-/opt/letterforge-data}"
OUT_DIR="${OUT_DIR:-/opt/letterforge-backups}"
KEEP="${KEEP:-14}"
mkdir -p "$OUT_DIR"
TS="$(date +%Y%m%d-%H%M%S)"; TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

if docker ps --format '{{.Names}}' | grep -qx letterforge; then
  # SQLite online-backup API: a clean snapshot even if the app is mid-write
  docker exec letterforge python -c "import sqlite3; s=sqlite3.connect('/data/letterforge.db'); d=sqlite3.connect('/data/.snapshot.db'); s.backup(d); d.close(); s.close()"
  mv "$DATA_DIR/.snapshot.db" "$TMP/letterforge.db"
else
  cp "$DATA_DIR/letterforge.db" "$TMP/letterforge.db"
fi
cp -a "$DATA_DIR/storage" "$TMP/storage"
tar -czf "$OUT_DIR/letterforge-$TS.tar.gz" -C "$TMP" .
echo "Backup written: $OUT_DIR/letterforge-$TS.tar.gz"
ls -1t "$OUT_DIR"/letterforge-*.tar.gz | tail -n +"$((KEEP + 1))" | xargs -r rm --   # keep the newest $KEEP
