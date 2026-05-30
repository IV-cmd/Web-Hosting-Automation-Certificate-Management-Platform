# Web Hosting Automation & Certificate Management Platform

A platform to automate deployment and lifecycle management of hosted web applications, integrating SSL certificate provisioning, renewal workflows, and environment-specific configuration management.

## Tech Stack

### Backend
- **Framework:** Flask
- **Database:** PostgreSQL
- **Authentication:** JWT
- **Kubernetes Integration:** Helm charts
- **Secrets Management:** HashiCorp Vault

### Frontend
- **Framework:** ReactJS
- **Styling:** Tailwind CSS
- **Real-time Updates:** WebSockets

### DevOps
- **Containerization:** Docker
- **Orchestration:** Kubernetes
- **Deployment Strategy:** Blue-green
- **CI/CD:** Jenkins
- **SSL Provider:** Let's Encrypt (Wildcard certificates)

### Features
- Automated SSL certificate provisioning and renewal
- Blue-green deployment with automated rollback on failure
- Nginx and Apache configuration management
- Docker container deployment automation
- Real-time deployment status monitoring
- Environment-specific configuration management

## Project Structure

```
windsurf-project/
├── backend/                 # Flask API
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API clients
│   │   └── utils/          # Utilities
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── helm/                   # Helm charts
│   └── web-hosting-platform/
├── jenkins/                # Jenkins pipeline configuration
├── k8s/                    # Kubernetes manifests
├── nginx-config/           # Nginx configuration templates
├── apache-config/          # Apache configuration templates
└── docker-compose.yml      # Local development
```

## Getting Started

### Prerequisites
- Docker
- Kubernetes cluster
- Helm
- PostgreSQL
- HashiCorp Vault
- Jenkins

### Local Development
```bash
# Start all services
docker-compose up -d

# Backend API: http://localhost:5000
# Frontend: http://localhost:3000
```

### Deployment
```bash
# Deploy to Kubernetes
helm install web-hosting-platform ./helm/web-hosting-platform
```

## License
MIT
