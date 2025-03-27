# Alfred: AI-Powered Assistance 

## 📋 Project Overview

Alfred is an advanced AI-powered assistant designed specifically , focusing on providing comprehensive support for [Company] solutions. The application leverages cutting-edge technologies to deliver intelligent, context-aware responses and streamline user interactions.

## 🚀 Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10
- **AI Engine**: LangChain, LangGraph
- **Embedding**: OpenAI Embeddings
- **Vector Store**: FAISS
- **Database**: PostgreSQL (Async SQLAlchemy)

### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS
- **Routing**: React Router
- **Build Tool**: Vite

### Containerization
- **Docker**
- **Docker Compose**

## 🔧 Key Features

- **Intelligent Retrieval**: Advanced RAG (Retrieval Augmented Generation) system
- **Context-Aware Responses**: AI tailored to Surface Tech's specific domain
- **Multi-Thread Chat Management**
- **Contact Management**
- **Email Integration**
- **Dynamic Chart Generation**

## 📦 Prerequisites

- Docker
- Docker Compose
- npm (for frontend development)
- Python 3.10+

## 🛠️ Installation & Setup

### Clone the Repository
```bash
git clone https://github.com/your-org/alfred.git
cd alfred
```

### Environment Configuration
1. Create a `.env` file in the backend directory
2. Add the following required environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=postgresql+asyncpg://postgres:admin@postgres_db:5432/alfred
   CONTACTS_URL=your_contacts_api_url
   CHART_URL=your_chart_generation_url
   ```

### Running the Application
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

## 📂 Project Structure
```
alfred/
│
├── backend/
│   ├── alfred_tools.py      # AI tools and utilities
│   ├── assistant.py         # AI assistant configuration
│   ├── main.py              # FastAPI application
│   ├── Dockerfile           # Backend Docker configuration
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React application
│   │   └── components/      # React components
│   ├── Dockerfile           # Frontend Docker configuration
│   └── package.json         # Frontend dependencies
│
└── docker-compose.yml       # Docker Compose configuration
```

## 🔐 Security Considerations
- Uses environment variables for sensitive information
- Implements secure API authentication
- Utilizes asyncio for non-blocking database operations

## 🧪 Testing
- Backend: Run pytest in the backend directory
- Frontend: Use React Testing Library

## 🔍 Development Workflow
1. Make changes to source code
2. Rebuild Docker containers
3. Test thoroughly
4. Commit and push changes

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

