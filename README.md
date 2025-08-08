# SuperMon - SDLC Automation Platform

A comprehensive Software Development Life Cycle automation platform using MCP (Model Context Protocol) servers and agentic framework with Gemini 2.5 Pro integration.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** - Required for the modular script system
- **Conda** (Miniconda or Anaconda) - [Download here](https://docs.conda.io/en/latest/miniconda.html)
- **Docker** (optional) - For database containers
- **Git** - Version control

### Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd SuperMon

# Make startup scripts executable
chmod +x start_all.sh supermon.py

# Setup environment and dependencies
./start_all.sh setup

# Start all services
./start_all.sh start

# Check status
./start_all.sh status
```

## 🛠️ Development Commands

```bash
# Run code quality checks
./start_all.sh quality

# Format code
./start_all.sh format

# Lint code
./start_all.sh lint

# Run tests
./start_all.sh test

# Stop all services
./start_all.sh stop

# Restart all services
./start_all.sh restart
```

## 📂 Project Structure

### Modular Script System
The project now uses a modular Python-based script system for better maintainability:

- `supermon.py` - Main Python script for managing all services
- `start_all.sh` - Shell wrapper around the Python script
- `scripts/` - Directory containing modular components:
  - `utils.py` - Utility functions
  - `environment.py` - Environment and dependency management
  - `database.py` - Database service management
  - `services.py` - Backend, frontend, and MCP server management

This modular approach makes it easier to maintain and extend the platform.

## 🏗️ Architecture

### **Multi-Agent System**
- **Requirements Agent**: Analyzes conversations and extracts requirements
- **Planning Agent**: Creates epics and user stories
- **Development Agent**: Manages code and deployment
- **Testing Agent**: Handles testing and quality assurance
- **Communication Agent**: Manages stakeholder communication

### **MCP Server Integration**
- **Slack**: Real-time messaging and notifications
- **WhatsApp**: Mobile communication
- **Webex**: Video conferencing and meetings
- **Notion**: Documentation and planning
- **GitHub**: Repository and issue management
- **PostgreSQL**: Database management
- **Redis**: Caching and sessions
- **Docker**: Containerization
- **Tl;dv**: Meeting recording and transcription

### **Technology Stack**
- **Backend**: FastAPI + Python 3.11
- **Frontend**: Next.js 14 + React 18
- **Database**: PostgreSQL + Redis
- **AI**: Gemini 2.5 Pro
- **Environment**: Conda
- **Code Quality**: Black, isort, ruff, mypy, pre-commit

## 🔧 Configuration

### Environment Setup
The platform uses conda for environment management. The `environment.yml` file defines all dependencies:

```yaml
name: supermon
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pip
  - nodejs=18
  - postgresql=15
  - redis=7
  - pip:
    - fastapi==0.104.1
    - uvicorn==0.24.0
    # ... other dependencies
```

### Required API Keys
Create a `.env` file with your API keys:

```env
# AI Services
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Communication Services
SLACK_BOT_TOKEN=your_slack_bot_token_here
WHATSAPP_API_KEY=your_whatsapp_api_key_here
WEBEX_ACCESS_TOKEN=your_webex_token_here

# Project Management
NOTION_API_KEY=your_notion_api_key_here
GITHUB_TOKEN=your_github_token_here

# Database
DATABASE_URL=postgresql://supermon:supermon123@localhost/supermon
REDIS_URL=redis://localhost:6379

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 Features

### **AI-Powered Requirements Analysis**
- Analyzes Slack/Webex conversations using Gemini 2.5 Pro
- Extracts functional, non-functional, and technical requirements
- Validates and prioritizes requirements automatically
- Generates comprehensive requirements summaries

### **Automated Project Planning**
- Creates project epics from analyzed requirements
- Generates user stories with acceptance criteria
- Estimates story points and effort using AI
- Maps dependencies automatically

### **Intelligent Meeting Management**
- Automated meeting scheduling with participant coordination
- Integration with Tl;dv for recording and transcription
- AI-powered action item extraction from meeting transcripts
- Automatic follow-up on action items

### **Multi-Channel Communication**
- **Slack**: Team collaboration and notifications
- **WhatsApp**: Stakeholder updates and mobile communication
- **Webex**: Video conferencing and meeting management
- **Email**: Formal communications and summaries

### **Development Automation**
- GitHub integration for repository management
- Automatic issue creation and tracking
- CI/CD pipeline integration
- AI-assisted code review and quality checks

### **Documentation & Knowledge Management**
- Notion integration for automated documentation
- AI-generated technical specifications
- Automatic API documentation generation
- Centralized knowledge base management

## 🎯 Workflow

1. **Requirements Gathering**: AI analyzes conversations from Slack/Webex
2. **UI Enhancement**: Additional requirements collected via web interface
3. **Epic Creation**: AI generates project epics and user stories
4. **Meeting Scheduling**: Automated meeting coordination
5. **Development Tracking**: Real-time progress monitoring
6. **Documentation**: Automated Notion documentation
7. **Communication**: Multi-channel stakeholder updates

## 🔍 Code Quality

The platform includes comprehensive code quality tools:

### **Python Code Quality**
- **Black**: Code formatting
- **isort**: Import sorting
- **ruff**: Fast Python linter
- **mypy**: Static type checking
- **pytest**: Testing framework
- **pre-commit**: Automated quality checks

### **Frontend Code Quality**
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **TypeScript**: Static type checking

### **Quality Commands**
```bash
# Run all quality checks
./start_all.sh quality

# Format code only
./start_all.sh format

# Lint code only
./start_all.sh lint

# Run tests only
./start_all.sh test
```

## 🚀 Deployment

### **Development Environment**
```bash
# Start all services
./start_all.sh start

# Access points
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

### **Production Environment**
```bash
# Build and deploy with Docker
docker-compose up -d

# Or deploy to cloud platforms
# - AWS ECS/Fargate
# - Google Cloud Run
# - Azure Container Instances
# - Heroku
```

## 📈 Monitoring & Observability

### **Health Checks**
- Application health endpoints
- Database connection monitoring
- MCP server status tracking
- Agent performance metrics

### **Logging**
- Structured logging with JSON format
- Log aggregation and analysis
- Error tracking and alerting
- Performance monitoring

### **Metrics**
- Project completion rates
- Agent performance metrics
- API response times
- User engagement analytics

## 🔐 Security

### **Authentication & Authorization**
- JWT-based authentication
- Role-based access control (RBAC)
- API key management for external services
- Secure token storage

### **Data Protection**
- Encrypted API communications
- Secure database connections
- Environment variable management
- Audit logging

### **API Security**
- Rate limiting
- Input validation
- CORS configuration
- Error handling without information leakage

## 🤝 Contributing

### **Development Setup**
```bash
# Clone and setup
git clone <repository-url>
cd SuperMon

# Setup conda environment
conda env create -f environment.yml
conda activate supermon

# Install pre-commit hooks
pre-commit install

# Run quality checks
./start_all.sh quality
```

### **Code Standards**
- Follow PEP 8 for Python code
- Use type hints throughout
- Write comprehensive tests
- Document all public APIs
- Use conventional commits

### **Testing**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

## 📚 Documentation

- **Setup Guide**: `docs/SETUP.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **API Documentation**: http://localhost:8000/docs
- **Code Quality**: See `.pre-commit-config.yaml`

## 🌐 Access Points

Once running, access the platform at:
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin Panel**: http://localhost:3000/admin

## 🐛 Troubleshooting

### **Common Issues**

#### **Conda Environment Issues**
```bash
# Recreate environment
conda env remove -n supermon
conda env create -f environment.yml
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL
docker ps | grep postgres
docker logs supermon-postgres

# Check Redis
docker ps | grep redis
docker logs supermon-redis
```

#### **Code Quality Issues**
```bash
# Fix formatting
black .
isort .

# Fix linting issues
ruff check --fix .

# Check types
mypy app/
```

### **Logs Location**
- Backend logs: `backend/logs/`
- Frontend logs: Browser console
- MCP server logs: `mcp_servers/*/logs/`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check `/docs` directory
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Slack**: Join our community Slack channel

---

**SuperMon** - Streamlining SDLC with AI-powered automation and multi-channel communication.