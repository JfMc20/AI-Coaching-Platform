# 🚀 Multi-Channel Proactive Coaching Platform

## 📋 Estado Actual: MVP Completamente Funcional

**Plataforma integral de coaching impulsada por IA** que permite a los creadores construir, desplegar y gestionar programas de coaching proactivos a través de múltiples canales. Combina inteligencia artificial con experiencia humana para entregar experiencias de coaching personalizadas y orientadas a resultados.

### ✅ Funcionalidades Implementadas
- 🏗️ **Arquitectura de Microservicios** completa y funcional
- 🐳 **Docker Multi-Stage Builds** optimizados para producción
- 🔒 **Autenticación JWT** robusta con multi-tenancy
- 🤖 **Motor de IA** con Ollama y ChromaDB integrados
- 📡 **API Gateway** con Nginx, rate limiting y CORS
- 💾 **Cache Redis** multi-tenant con prevención de stampede
- 🔍 **Health Checks** dinámicos y confiables
- 📊 **Scripts de Monitoreo** automatizados
- 📚 **Documentación** completa y actualizada

## Vision

Transform the creator economy by providing a "Results as a Service" platform that goes beyond traditional chatbot builders to deliver proactive, intelligent coaching that drives real behavioral change and measurable outcomes.

## Key Differentiators

- **Proactive Engagement**: AI-driven system that initiates conversations and interventions based on user behavior and progress
- **Multi-Channel Delivery**: Seamless coaching experience across web widgets, messaging apps, and mobile applications
- **Visual Program Builder**: Intuitive drag-and-drop interface for creating complex coaching workflows
- **Dynamic User Profiling**: AI-powered system that learns and adapts to individual user preferences and behaviors
- **Results-Focused**: Built-in analytics and gamification to track and drive measurable outcomes

## Technology Stack

- **Backend**: FastAPI (Python) with microservices architecture
- **AI/ML**: LangChain for AI workflows, Ollama for LLM serving, ChromaDB for vector storage
- **Database**: PostgreSQL for primary data, ChromaDB for vector embeddings
- **Frontend**: React for creator dashboard, React Native for mobile app
- **Infrastructure**: Docker containerization, cloud-native deployment
- **Integrations**: WhatsApp Business API, Telegram Bot API, payment processors

## Platform Dependencies

### System Requirements

The platform requires certain native libraries and system packages for proper functionality:

#### Debian/Ubuntu
```bash
# Update package list
sudo apt-get update

# Install required system packages
sudo apt-get install -y \
    build-essential \
    libmagic1 \
    libmagic-dev \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    pkg-config \
    curl \
    git \
    nodejs \
    npm
```

#### CentOS/RHEL/Fedora
```bash
# For CentOS/RHEL
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    file-devel \
    openssl-devel \
    libffi-devel \
    postgresql-devel \
    python3-devel \
    python3-pip \
    pkgconfig \
    curl \
    git \
    nodejs \
    npm

# For Fedora
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y \
    file-devel \
    openssl-devel \
    libffi-devel \
    postgresql-devel \
    python3-devel \
    python3-pip \
    pkgconfig \
    curl \
    git \
    nodejs \
    npm
```

#### macOS
```bash
# Install Xcode command line tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install \
    libmagic \
    openssl \
    libffi \
    postgresql \
    pkg-config \
    python@3.11 \
    node \
    npm
```

#### Windows
```powershell
# Install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Install Git for Windows
# Download from: https://git-scm.com/download/win

# Install Python 3.11+ from python.org
# Ensure "Add Python to PATH" is checked during installation
```

### Package Dependencies Explained

| Package | Purpose | Required For |
|---------|---------|--------------|
| `build-essential` | Compilation tools (gcc, make, etc.) | Building Python packages with C extensions |
| `libmagic1` / `libmagic-dev` | File type detection | `python-magic` package for document processing |
| `libssl-dev` | SSL/TLS support | Secure connections, cryptography packages |
| `libffi-dev` | Foreign Function Interface | `cryptography` and other security packages |
| `libpq-dev` | PostgreSQL development headers | `psycopg2` and other PostgreSQL packages |
| `python3-dev` | Python development headers | Building Python C extensions |
| `python3-pip` | Python package installer | Installing Python packages |
| `python3-venv` | Python virtual environments | Creating isolated Python environments |
| `pkg-config` | Package configuration | Finding libraries during compilation |
| `nodejs` / `npm` | JavaScript runtime and package manager | Frontend development and build tools |

### Development Environment Recommendation

**🐳 Docker is the preferred development environment** as it simplifies setup and avoids system-level package conflicts. The host package instructions above are provided for developers who cannot use Docker or prefer native development.

```bash
# Recommended: Use Docker for development
docker-compose up -d

# Alternative: Native development (requires system packages above)
./scripts/bootstrap-system.sh
```

### Automated Setup Script

Use our bootstrap script to automatically install system dependencies:

```bash
# Make script executable
chmod +x scripts/bootstrap-system.sh

# Run bootstrap script
./scripts/bootstrap-system.sh

# Or for specific OS
./scripts/bootstrap-system.sh --os ubuntu
./scripts/bootstrap-system.sh --os centos
./scripts/bootstrap-system.sh --os macos
```

## Quick Start

### For Development

1. **Prerequisites**: Docker Desktop, Docker Compose, Git, System Dependencies (see above)
2. **Setup Environment**:
   ```bash
   # Clone repository
   git clone <repository-url>
   cd mvp-coaching-ai-platform
   
   # Install system dependencies
   ./scripts/bootstrap-system.sh
   
   # Install Python dependencies
   pip install -r requirements.txt
   pip install -e ".[dev]"  # For development dependencies
   
   # Setup development environment
   make setup  # Linux/macOS
   # or
   scripts\setup-dev.bat  # Windows
   ```
3. **Access Services**:
   - Auth Service: http://localhost:8001/docs
   - Creator Hub: http://localhost:8002/docs
   - AI Engine: http://localhost:8003/docs
   - Channel Service: http://localhost:8004/docs

### For Documentation Review

1. **Documentation Review**: Start with the comprehensive documentation in the `/docs` directory
2. **Architecture Understanding**: Review system architecture and technology decisions
3. **API Exploration**: Examine API specifications for integration requirements

## Documentation Structure

```
docs/
├── 01-product/              # Business requirements and product specifications
├── 02-architecture/         # Technical architecture and system design
├── 03-api-specifications/   # Complete API documentation
├── 04-user-experience/      # UX specifications and design guidelines
├── 05-business-logic/       # Core business logic and algorithms
├── 06-ai-ml-specifications/ # AI/ML implementation details
├── 07-development-guidelines/ # Coding standards and workflows
├── 08-project-management/   # Roadmap, features, and project planning
├── 09-compliance-and-legal/ # Privacy, terms, and content policies
└── 10-technical-specifications/ # Performance and infrastructure requirements
```

## Core Components

### Creator Hub (SaaS Dashboard)
- Knowledge base management
- Visual program builder
- Multi-channel configuration
- Analytics and insights dashboard
- Proactive engagement engine

### User Channels
- **Web Widget**: Embeddable chat interface for websites
- **Messaging Apps**: WhatsApp and Telegram integration
- **Mobile App**: Branded "Compañero" app with habit tracking and gamification

### AI Engine
- RAG-powered knowledge retrieval
- Conversational AI with context awareness
- Proactive engagement algorithms
- Dynamic user profiling and personalization

## Getting Started

For detailed implementation guidance, begin with:

1. [Product Requirements](docs/01-product/product-requirements.md)
2. [System Architecture](docs/02-architecture/system-architecture.md)
3. [Development Roadmap](docs/08-project-management/development-roadmap.md)

## Development

### Project Structure

```
mvp-coaching-ai-platform/
├── services/
│   ├── auth-service/           # Authentication & authorization
│   ├── creator-hub-service/    # Creator management & content
│   ├── ai-engine-service/      # AI processing & RAG
│   └── channel-service/        # Real-time communication
├── shared/                     # Shared models & utilities
├── scripts/                    # Setup & deployment scripts
├── nginx/                      # API Gateway configuration
├── docker-compose.yml          # Development environment
└── Makefile                   # Development commands
```

### Dependency Management

The project uses a tiered approach to dependency management:

- **`requirements.txt`**: Core dependencies currently used in the codebase
- **`requirements-full.txt`**: Complete dependencies for full platform implementation
- **`pyproject.toml`**: Development dependencies and project configuration

```bash
# Install core dependencies only
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Install full platform dependencies (when implementing complete features)
pip install -r requirements-full.txt
```

### Available Commands

```bash
make setup          # Initial environment setup
make up             # Start all services
make down           # Stop all services
make logs           # View service logs
make test           # Run tests
make format         # Format code
make lint           # Run linting
make clean          # Clean containers and volumes
```

### Service Architecture

The platform uses a microservices architecture with:
- **FastAPI** for all backend services
- **PostgreSQL** with Row Level Security for multi-tenancy
- **Redis** for caching and session management
- **Ollama** for local LLM serving
- **ChromaDB** for vector storage and semantic search

## Contributing

Please review the [development guidelines](docs/07-development-guidelines/) before contributing to ensure consistency with project standards and workflows.

## License

[License information to be added]