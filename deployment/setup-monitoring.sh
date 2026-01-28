#!/bin/bash

# =============================================================================
# NOJIRA Monitoring Setup Script
# =============================================================================
# This script sets up automated monitoring for NOJIRA containers
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

print_header "Setting Up Monitoring"

# Create monitoring script
cat > /opt/nojira/monitor.sh <<'EOF'
#!/bin/bash
LOG=/opt/nojira/monitor.log

# Check if containers are running
for container in nojira-db nojira-backend nojira-frontend; do
    if ! docker ps | grep -q $container; then
        echo "$(date): $container is DOWN - restarting" >> $LOG
        cd /opt/nojira && docker-compose -f docker-compose.prod.yml up -d $container
    fi
done

# Check disk space
DISK=$(df -h /opt/nojira | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK -gt 85 ]; then
    echo "$(date): Disk usage HIGH: ${DISK}%" >> $LOG
fi

# Check backend health
if ! curl -f -s http://localhost:8007/api/health > /dev/null 2>&1; then
    echo "$(date): Backend health check FAILED" >> $LOG
    cd /opt/nojira && docker-compose -f docker-compose.prod.yml restart backend
fi
EOF

chmod +x /opt/nojira/monitor.sh
print_success "Monitoring script created"

# Add to crontab (every 5 minutes)
(crontab -l 2>/dev/null | grep -v '/opt/nojira/monitor.sh'; echo "*/5 * * * * /opt/nojira/monitor.sh") | crontab -
print_success "Cron job added (runs every 5 minutes)"

# Create log file
touch /opt/nojira/monitor.log
print_success "Monitor log created"

echo ""
echo "Monitoring enabled!"
echo "Log file: /opt/nojira/monitor.log"
echo "Check interval: Every 5 minutes"
echo ""
echo "To view monitoring log:"
echo "  tail -f /opt/nojira/monitor.log"
