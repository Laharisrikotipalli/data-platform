#!/bin/bash
# backup.sh — Run this from the repo root:
#   bash backup.sh
# Or inside the warehouse container:
#   docker-compose exec postgres-warehouse /backups/backup.sh

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$BACKUP_DIR"

echo "Starting backup at $TIMESTAMP..."

# Backup warehouse (primary)
docker exec postgres-warehouse pg_dump \
    -U warehouseuser \
    warehousedb \
    > "$BACKUP_DIR/warehouse_backup_${TIMESTAMP}.sql"

echo "Warehouse backup saved: $BACKUP_DIR/warehouse_backup_${TIMESTAMP}.sql"

# Backup source DB
docker exec postgres-source pg_dump \
    -U sourceuser \
    sourcedb \
    > "$BACKUP_DIR/source_backup_${TIMESTAMP}.sql"

echo "Source backup saved: $BACKUP_DIR/source_backup_${TIMESTAMP}.sql"
echo "Backup completed at $TIMESTAMP"
