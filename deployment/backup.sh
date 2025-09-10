#!/bin/bash

# Asset Management System Backup Script
# Run daily via cron: 0 2 * * * /opt/asset_management/deployment/backup.sh

set -e

# Configuration
BACKUP_DIR="/opt/backups/asset_management"
APP_DIR="/opt/asset_management"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Database configuration (from .env file)
source $APP_DIR/.env

# Create backup directory
mkdir -p $BACKUP_DIR

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $BACKUP_DIR/backup.log
}

log "Starting backup process..."

# Database backup
log "Backing up database..."
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/db_$DATE.sql
if [ $? -eq 0 ]; then
    log "Database backup completed successfully"
    gzip $BACKUP_DIR/db_$DATE.sql
else
    log "Database backup failed!"
    exit 1
fi

# Media files backup
log "Backing up media files..."
if [ -d "$APP_DIR/media" ]; then
    tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $APP_DIR media/
    if [ $? -eq 0 ]; then
        log "Media files backup completed successfully"
    else
        log "Media files backup failed!"
        exit 1
    fi
else
    log "Media directory not found, skipping media backup"
fi

# Configuration backup
log "Backing up configuration files..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz -C $APP_DIR .env gunicorn.conf.py
if [ $? -eq 0 ]; then
    log "Configuration backup completed successfully"
else
    log "Configuration backup failed!"
    exit 1
fi

# Clean old backups
log "Cleaning old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup.log" -mtime +30 -delete

# Backup verification
log "Verifying backups..."
DB_BACKUP_SIZE=$(stat -c%s "$BACKUP_DIR/db_$DATE.sql.gz")
if [ $DB_BACKUP_SIZE -gt 1000 ]; then
    log "Database backup verification passed (size: $DB_BACKUP_SIZE bytes)"
else
    log "Database backup verification failed (size too small: $DB_BACKUP_SIZE bytes)"
    exit 1
fi

log "Backup process completed successfully"

# Optional: Upload to remote storage (uncomment and configure as needed)
# log "Uploading to remote storage..."
# rsync -avz $BACKUP_DIR/ user@backup-server:/backups/asset_management/
# aws s3 sync $BACKUP_DIR s3://your-backup-bucket/asset_management/

log "All backup operations completed"