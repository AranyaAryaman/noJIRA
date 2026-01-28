#!/bin/bash

# =============================================================================
# NOJIRA Systemd Auto-Start Setup Script
# =============================================================================
# This script enables auto-start of NOJIRA on EC2 reboot
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

print_header "Setting Up Systemd Service"

# Create systemd service file
sudo tee /etc/systemd/system/nojira.service > /dev/null <<'EOF'
[Unit]
Description=NOJIRA Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/nojira
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service file created"

# Reload systemd
sudo systemctl daemon-reload
print_success "Systemd reloaded"

# Enable service
sudo systemctl enable nojira.service
print_success "Service enabled for auto-start"

# Check status
sudo systemctl status nojira.service --no-pager || true

echo ""
echo "Systemd service configured!"
echo ""
echo "Useful commands:"
echo "  Start:   sudo systemctl start nojira"
echo "  Stop:    sudo systemctl stop nojira"
echo "  Restart: sudo systemctl restart nojira"
echo "  Status:  sudo systemctl status nojira"
echo "  Logs:    sudo journalctl -u nojira -f"
