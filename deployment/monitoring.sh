#!/bin/bash

# Asset Management System Monitoring Script
# Run every 5 minutes via cron: */5 * * * * /opt/asset_management/deployment/monitoring.sh

# Configuration
APP_NAME="asset-management"
LOG_FILE="/var/log/asset_management/monitoring.log"
ALERT_EMAIL="admin@your-domain.com"

# Create log directory if it doesn't exist
mkdir -p $(dirname $LOG_FILE)

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

# Send alert function
send_alert() {
    local subject="$1"
    local message="$2"
    echo "$message" | mail -s "$subject" $ALERT_EMAIL
    log "ALERT: $subject - $message"
}

# Check service status
check_service() {
    local service_name="$1"
    if ! systemctl is-active --quiet $service_name; then
        send_alert "Service Down: $service_name" "Service $service_name is not running on $(hostname)"
        systemctl restart $service_name
        log "Attempted to restart $service_name"
    else
        log "Service $service_name is running"
    fi
}

# Check disk space
check_disk_space() {
    local threshold=85
    local usage=$(df /opt/asset_management | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $usage -gt $threshold ]; then
        send_alert "Disk Space Warning" "Disk usage is at ${usage}% on $(hostname)"
    fi
    log "Disk usage: ${usage}%"
}

# Check memory usage
check_memory() {
    local threshold=90
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ $usage -gt $threshold ]; then
        send_alert "Memory Usage Warning" "Memory usage is at ${usage}% on $(hostname)"
    fi
    log "Memory usage: ${usage}%"
}

# Check database connectivity
check_database() {
    source /opt/asset_management/.env
    if ! mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD -e "SELECT 1;" $DB_NAME > /dev/null 2>&1; then
        send_alert "Database Connection Failed" "Cannot connect to database on $(hostname)"
    else
        log "Database connection successful"
    fi
}

# Check Redis connectivity
check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        send_alert "Redis Connection Failed" "Cannot connect to Redis on $(hostname)"
        systemctl restart redis
        log "Attempted to restart Redis"
    else
        log "Redis connection successful"
    fi
}

# Check application response
check_app_response() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/auth/profile/ -H "Authorization: Bearer dummy")
    if [ "$response" != "401" ]; then  # 401 is expected without valid token
        send_alert "Application Not Responding" "Application is not responding correctly on $(hostname)"
    else
        log "Application responding correctly"
    fi
}

# Check SSL certificate expiry
check_ssl_expiry() {
    local domain="your-domain.com"
    local days_until_expiry=$(echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2 | xargs -I {} date -d {} +%s)
    local current_date=$(date +%s)
    local days_left=$(( ($days_until_expiry - $current_date) / 86400 ))
    
    if [ $days_left -lt 30 ]; then
        send_alert "SSL Certificate Expiring" "SSL certificate for $domain expires in $days_left days"
    fi
    log "SSL certificate expires in $days_left days"
}

# Main monitoring checks
log "Starting monitoring checks..."

check_service "$APP_NAME"
check_service "$APP_NAME-celery"
check_service "$APP_NAME-celerybeat"
check_service "nginx"
check_service "mysql"
check_service "redis"

check_disk_space
check_memory
check_database
check_redis
check_app_response
check_ssl_expiry

log "Monitoring checks completed"

# Rotate log file if it gets too large (>10MB)
if [ -f $LOG_FILE ] && [ $(stat -c%s $LOG_FILE) -gt 10485760 ]; then
    mv $LOG_FILE $LOG_FILE.old
    log "Log file rotated"
fi