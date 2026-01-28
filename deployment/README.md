# NOJIRA Deployment Files

This folder contains all production deployment files for deploying NOJIRA to EC2.

## Files

- **deploy-ec2.sh** - Main deployment script (auto-generates secrets, builds & starts containers)
- **docker-compose.prod.yml** - Production Docker Compose configuration
- **setup-backups.sh** - Automated daily database/uploads backups
- **setup-monitoring.sh** - Container health monitoring (every 5 min)
- **setup-systemd.sh** - Auto-start on EC2 reboot
- **DEPLOYMENT.md** - Complete deployment guide

## Quick Deploy

On your EC2 server at `/opt/nojira`:

```bash
# Make scripts executable
chmod +x deployment/*.sh

# Deploy
./deployment/deploy-ec2.sh deploy

# Setup automation (optional)
./deployment/setup-backups.sh
./deployment/setup-monitoring.sh
./deployment/setup-systemd.sh
```

## What Gets Deployed

- **Frontend**: nginx container on port 9000 (accessible via ALB)
- **Backend**: FastAPI container on port 9001 (localhost only)
- **Database**: PostgreSQL 15 on port 9002 (localhost only)

All services run in Docker with health checks, restart policies, and isolated networking.

For full details, see [DEPLOYMENT.md](./DEPLOYMENT.md).
