#!/bin/bash

# =============================================================================
# NOJIRA Automated Backups Setup Script
# =============================================================================
# This script sets up automated daily backups for NOJIRA
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_header "Setting Up Automated Backups"

# Create backup script
cat > /opt/nojira/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/opt/nojira/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec nojira-db pg_dump -U nojira_user nojira | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup uploads
tar czf $BACKUP_DIR/uploads_$DATE.tar.gz -C /opt/nojira uploads 2>/dev/null || true

# Backup environment file
cp /opt/nojira/.env $BACKUP_DIR/env_$DATE.backup 2>/dev/null || true

# Keep last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "env_*.backup" -mtime +7 -delete

echo "$(date): Backup completed" >> $BACKUP_DIR/backup.log
EOF

chmod +x /opt/nojira/backup.sh
print_success "Backup script created"

# Add to crontab (3 AM daily)
(crontab -l 2>/dev/null | grep -v '/opt/nojira/backup.sh'; echo "0 3 * * * /opt/nojira/backup.sh") | crontab -
print_success "Cron job added (runs daily at 3 AM)"

# Test backup
print_header "Running Test Backup"
/opt/nojira/backup.sh
print_success "Test backup completed"

# Show backup location
echo ""
echo "Backups will be stored in: /opt/nojira/backups/"
echo "Retention: 7 days"
echo "Schedule: Daily at 3:00 AM"
echo ""
echo "To restore database:"
echo "  gunzip -c /opt/nojira/backups/db_YYYYMMDD_HHMMSS.sql.gz | docker exec -i nojira-db psql -U nojira_user -d nojira"
