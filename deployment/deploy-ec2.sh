#!/bin/bash

# =============================================================================
# NOJIRA EC2 Deployment Script
# =============================================================================
# This script deploys NOJIRA to EC2 using Docker Compose
# Run this script on your EC2 instance
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_requirements() {
    print_header "Checking Requirements"

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Run: sudo yum install -y docker && sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker is installed"

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Run: sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
        echo "     sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
    fi
    print_success "Docker Compose is installed"

    # Check if Docker service is running
    if ! docker info &> /dev/null; then
        print_error "Docker service is not running. Starting Docker..."
        sudo systemctl start docker
        sudo systemctl enable docker
    fi
    print_success "Docker service is running"
}

generate_secrets() {
    print_header "Generating Secure Secrets"

    # Generate SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    print_success "Generated SECRET_KEY"

    # Generate DB_PASSWORD
    DB_PASSWORD=$(openssl rand -hex 32)
    print_success "Generated DB_PASSWORD"

    echo ""
    echo "Your secrets (save these securely):"
    echo "SECRET_KEY=$SECRET_KEY"
    echo "DB_PASSWORD=$DB_PASSWORD"
    echo ""
}

create_env_file() {
    print_header "Creating Environment File"

    if [ -f "$ENV_FILE" ]; then
        print_warning "Environment file already exists. Backing up..."
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d%H%M%S)"
    fi

    cat > "$ENV_FILE" <<EOF
# Database Configuration
POSTGRES_USER=nojira_user
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=nojira

# Database URL (internal Docker network)
DATABASE_URL=postgresql://nojira_user:${DB_PASSWORD}@db:5432/nojira

# Backend Configuration
SECRET_KEY=${SECRET_KEY}
UPLOAD_DIR=/app/uploads
ENVIRONMENT=production

# CORS Configuration
ALLOWED_ORIGINS=https://ops.hushtalent.io

# Frontend URL
FRONTEND_URL=https://ops.hushtalent.io

# Frontend Build-time Variables
VITE_API_BASE_URL=https://ops.hushtalent.io
EOF

    chmod 600 "$ENV_FILE"
    print_success "Environment file created and secured"
}

create_directories() {
    print_header "Creating Data Directories"

    mkdir -p data/postgres
    mkdir -p uploads
    mkdir -p backups

    print_success "Data directories created"
}

stop_services() {
    print_header "Stopping Existing Services"

    if docker-compose -f "$COMPOSE_FILE" ps -q 2>/dev/null | grep -q .; then
        docker-compose -f "$COMPOSE_FILE" down
        print_success "Stopped existing services"
    else
        print_success "No existing services to stop"
    fi
}

build_services() {
    print_header "Building Services"

    docker-compose -f "$COMPOSE_FILE" build --no-cache
    print_success "Services built successfully"
}

start_services() {
    print_header "Starting Services"

    docker-compose -f "$COMPOSE_FILE" up -d
    print_success "Services started"
}

wait_for_health() {
    print_header "Waiting for Services to be Healthy"

    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))
        echo -n "Attempt $attempt/$max_attempts: Checking health... "

        # Check if backend is responding
        if curl -f -s http://localhost:8007/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}Backend is healthy!${NC}"
            break
        else
            echo -e "${YELLOW}Not ready yet${NC}"
            sleep 5
        fi
    done

    if [ $attempt -eq $max_attempts ]; then
        print_warning "Services may not be healthy yet. Check logs for details."
    fi
}

show_status() {
    print_header "Service Status"
    docker-compose -f "$COMPOSE_FILE" ps
}

test_endpoints() {
    print_header "Testing Endpoints"

    # Test backend
    if curl -f -s http://localhost:8007/api/health > /dev/null; then
        print_success "Backend is responding"
    else
        print_error "Backend is not responding"
    fi

    # Test frontend
    if curl -f -s http://localhost/ > /dev/null; then
        print_success "Frontend is responding"
    else
        print_error "Frontend is not responding"
    fi

    # Test database
    if docker exec nojira-db pg_isready -U nojira_user > /dev/null 2>&1; then
        print_success "Database is healthy"
    else
        print_error "Database is not healthy"
    fi
}

show_completion() {
    print_header "Deployment Complete!"

    # Get EC2 public IP (if available)
    local public_ip=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

    echo ""
    echo -e "${GREEN}Your NOJIRA platform is now running!${NC}"
    echo ""
    echo "Access your services at:"
    echo "  Frontend: http://$public_ip/"
    echo "  Backend API: http://$public_ip/api/"
    echo "  Health Check: http://$public_ip/api/health"
    echo ""
    echo "Container Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "Useful commands:"
    echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  Check status: docker-compose -f $COMPOSE_FILE ps"
    echo "  Restart service: docker-compose -f $COMPOSE_FILE restart <service-name>"
    echo "  Stop all: docker-compose -f $COMPOSE_FILE down"
    echo ""

    if [ "$public_ip" != "localhost" ]; then
        print_warning "Next steps:"
        echo "  1. Configure ALB to forward ops.hushtalent.io to this EC2 instance (port 80)"
        echo "  2. Update Route 53 DNS: ops.hushtalent.io → ALB"
        echo "  3. Request/configure SSL certificate in ACM for ops.hushtalent.io"
        echo "  4. Setup automated backups (run ./setup-backups.sh)"
        echo "  5. Setup monitoring (run ./setup-monitoring.sh)"
        echo "  6. Enable auto-start on reboot (run ./setup-systemd.sh)"
    fi
}

# Main execution
main() {
    echo ""
    print_header "NOJIRA EC2 Deployment"
    echo ""

    case "${1:-deploy}" in
        deploy)
            check_requirements
            generate_secrets
            create_env_file
            create_directories
            stop_services
            build_services
            start_services
            wait_for_health
            show_status
            test_endpoints
            show_completion
            ;;
        restart)
            print_header "Restarting Services"
            docker-compose -f "$COMPOSE_FILE" restart
            wait_for_health
            show_status
            ;;
        stop)
            print_header "Stopping Services"
            docker-compose -f "$COMPOSE_FILE" down
            print_success "All services stopped"
            ;;
        logs)
            docker-compose -f "$COMPOSE_FILE" logs -f
            ;;
        status)
            show_status
            test_endpoints
            ;;
        update)
            print_header "Updating Services"
            git pull
            stop_services
            build_services
            start_services
            wait_for_health
            show_status
            ;;
        *)
            echo "Usage: $0 {deploy|restart|stop|logs|status|update}"
            echo ""
            echo "Commands:"
            echo "  deploy  - Full deployment (default)"
            echo "  restart - Restart all services"
            echo "  stop    - Stop all services"
            echo "  logs    - View service logs"
            echo "  status  - Show service status and test endpoints"
            echo "  update  - Pull latest code and redeploy"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
