# SuperMon SDLC Automation Platform - Setup Guide

## 🚀 Quick Start

The fastest way to get SuperMon running is using our automated startup script:

```bash
# Make the script executable (if not already)
chmod +x start_all.sh

# Start all services
./start_all.sh start

# Check status
./start_all.sh status

# Stop all services
./start_all.sh stop
```

## 📋 Prerequisites

### Required Software
- **Python 3.11+** - Backend and AI services
- **Node.js 18+** - Frontend development
- **Docker** (optional) - Database containers
- **Git** - Version control

### Required API Keys
- **Gemini 2.5 Pro API Key** - AI text, voice, image, video generation
- **Slack Bot Token** - Communication and notifications
- **WhatsApp Business API** - Mobile communication
- **Webex API Token** - Video conferencing
- **Notion API Key** - Documentation and planning
- **GitHub Personal Access Token** - Repository management

## 🛠️ Manual Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd SuperMon
```

### 2. Backend Setup

#### Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Database Setup
```bash
# Using Docker (recommended)
docker run -d --name supermon-postgres \
  -e POSTGRES_DB=supermon \
  -e POSTGRES_USER=supermon \
  -e POSTGRES_PASSWORD=supermon123 \
  -p 5432:5432 \
  postgres:15

docker run -d --name supermon-redis \
  -p 6379:6379 \
  redis:7-alpine

# Or install locally
# PostgreSQL: https://www.postgresql.org/download/
# Redis: https://redis.io/download
```

#### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

Required environment variables:
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

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. MCP Servers Setup

The platform uses MCP (Model Context Protocol) servers for external integrations:

#### Slack MCP
```bash
cd mcp_servers/slack_mcp
python slack_mcp.py
```

#### WhatsApp MCP
```bash
cd mcp_servers/whatsapp_mcp
python whatsapp_mcp.py
```

#### Notion MCP
```bash
cd mcp_servers/notion_mcp
python notion_mcp.py
```

#### GitHub MCP
```bash
cd mcp_servers/github_mcp
python github_mcp.py
```

## 🔧 API Key Setup

### Gemini 2.5 Pro
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env`: `GEMINI_API_KEY=your_key_here`

### Slack Bot
1. Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Add bot token scopes: `chat:write`, `channels:read`, `users:read`
3. Install app to workspace
4. Add to `.env`: `SLACK_BOT_TOKEN=xoxb-your-token`

### WhatsApp Business
1. Set up WhatsApp Business API
2. Get API key from Meta Developer Console
3. Add to `.env`: `WHATSAPP_API_KEY=your_key_here`

### Webex
1. Create Webex app at [developer.webex.com](https://developer.webex.com)
2. Generate access token
3. Add to `.env`: `WEBEX_ACCESS_TOKEN=your_token_here`

### Notion
1. Go to [notion.so/my-integrations](https://notion.so/my-integrations)
2. Create new integration
3. Add to `.env`: `NOTION_API_KEY=secret_your_key_here`

### GitHub
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Generate new token with repo, issues, workflow permissions
3. Add to `.env`: `GITHUB_TOKEN=ghp_your_token_here`

## 🚀 Starting Services

### Option 1: Automated Script (Recommended)
```bash
./start_all.sh start
```

### Option 2: Manual Start

#### Backend
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd frontend
npm run dev
```

#### MCP Servers (in separate terminals)
```bash
# Terminal 1
cd mcp_servers/slack_mcp
python slack_mcp.py

# Terminal 2
cd mcp_servers/whatsapp_mcp
python whatsapp_mcp.py

# Terminal 3
cd mcp_servers/notion_mcp
python notion_mcp.py

# Terminal 4
cd mcp_servers/github_mcp
python github_mcp.py
```

## 🌐 Access Points

Once all services are running:

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin Panel**: http://localhost:3000/admin

## 🔍 Verification

### Check Service Status
```bash
./start_all.sh status
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Get projects
curl http://localhost:8000/api/v1/projects

# Get agent status
curl http://localhost:8000/api/v1/agents/status
```

### Test MCP Connections
```bash
# Check MCP status
curl http://localhost:8000/api/v1/communication/mcp-status
```

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection
psql -h localhost -U supermon -d supermon
```

#### Frontend Build Errors
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Python Import Errors
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### MCP Server Connection Issues
```bash
# Check if MCP servers are running
ps aux | grep mcp

# Check MCP server logs
tail -f mcp_servers/*/logs/*.log
```

### Logs Location
- Backend logs: `backend/logs/`
- Frontend logs: Browser console
- MCP server logs: `mcp_servers/*/logs/`

### Reset Everything
```bash
# Stop all services
./start_all.sh stop

# Remove containers
docker stop supermon-postgres supermon-redis
docker rm supermon-postgres supermon-redis

# Remove virtual environment
rm -rf venv

# Remove node modules
rm -rf frontend/node_modules

# Start fresh
./start_all.sh setup
./start_all.sh start
```

## 📚 Next Steps

1. **Configure API Keys**: Update `.env` with your actual API keys
2. **Create First Project**: Use the dashboard to create your first SDLC project
3. **Test Integrations**: Verify Slack, WhatsApp, and other integrations work
4. **Customize Workflows**: Modify agent behaviors for your specific needs
5. **Scale Up**: Add more MCP servers and agents as needed

## 🤝 Support

- **Documentation**: Check `/docs` directory
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Slack**: Join our community Slack channel

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 