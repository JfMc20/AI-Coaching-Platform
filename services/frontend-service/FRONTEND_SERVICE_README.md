# Frontend Service - Multi-Channel AI Coaching Platform

**Visual Program Builder & Testing Interface**

## 🚀 Overview

The Frontend Service provides a React-based visual interface for the Multi-Channel AI Coaching Platform, featuring a drag-and-drop canvas built with React Flow for creating and testing coaching programs.

## 🏗️ Architecture

### Technology Stack
- **Framework**: Next.js 15 with TypeScript
- **Canvas Library**: React Flow (@xyflow/react)
- **State Management**: Zustand
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Port**: 8006

### Key Features
- ✅ **Protected Development Routes** - Authentication-protected interface for internal use
- ✅ **Visual Program Builder** - Drag-and-drop canvas for creating coaching flows
- ✅ **Custom React Flow Nodes** - Specialized nodes for different step types
- ✅ **Real-time Validation** - Program validation with error/warning indicators
- ✅ **API Integration** - Complete integration with backend services
- ✅ **Auto-save Functionality** - Automatic saving of program changes
- ✅ **Multi-tenant Support** - Creator-based isolation and authentication

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with environment validation
│   ├── page.tsx           # Landing page with dev mode detection
│   └── testing/           # Protected testing interface
├── components/            # React components
│   ├── auth/              # Authentication components
│   │   └── DevAuthWrapper.tsx
│   └── canvas/            # Canvas-related components
│       ├── ProgramCanvas.tsx      # Main React Flow canvas
│       ├── CanvasToolbar.tsx      # Node palette & actions
│       ├── NodeSidebar.tsx        # Node configuration panel
│       ├── ValidationPanel.tsx    # Program validation display
│       ├── EdgeInfoPanel.tsx      # Connection information
│       └── nodes/                 # Custom React Flow nodes
├── stores/                # Zustand state management
│   ├── authStore.ts       # Authentication state
│   └── canvasStore.ts     # Canvas state management
├── hooks/                 # Custom React hooks
│   ├── usePrograms.ts     # Program management
│   ├── useKnowledge.ts    # Knowledge & personality management
│   ├── useProgramValidation.ts  # Program validation logic
│   ├── useCanvasAPI.ts    # Canvas-API integration
│   └── index.ts           # Hook exports
├── lib/                   # Utility libraries
│   └── apiClient.ts       # Axios-based API client
├── config/                # Configuration
│   └── environment.ts     # Environment management
└── types/                 # TypeScript definitions
    └── index.ts           # Shared type definitions
```

## 🎯 Key Components

### 1. Visual Program Builder
- **Drag-and-drop interface** for creating coaching programs
- **6 node types**: Message, Task, Survey, Wait, Condition, Trigger
- **Real-time connections** between program steps
- **Visual validation** with error/warning indicators

### 2. Protected Development Interface
- **Authentication-protected routes** for internal use only
- **Development access codes** for secure access
- **Environment-based route protection**
- **Session-based authentication**

### 3. API Integration Layer
- **Complete backend integration** with all 4 services
- **Automatic token refresh** and error handling  
- **Real-time synchronization** with backend state
- **Auto-save functionality** with conflict resolution

### 4. State Management
- **Zustand stores** for canvas and authentication state
- **Real-time validation** with comprehensive error checking
- **Optimistic updates** with rollback on errors
- **Persistent state** across browser sessions

## 🔧 Development Commands

```bash
# Install dependencies
npm install

# Start development server (port 8006)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## 🐳 Docker Deployment

```bash
# Build Docker image
docker build -t frontend-service .

# Run container
docker run -p 8006:3000 \
  -e NEXT_PUBLIC_AUTH_SERVICE_URL=http://auth-service:8001 \
  -e NEXT_PUBLIC_CREATOR_HUB_SERVICE_URL=http://creator-hub-service:8002 \
  -e NEXT_PUBLIC_AI_ENGINE_SERVICE_URL=http://ai-engine-service:8003 \
  -e NEXT_PUBLIC_CHANNEL_SERVICE_URL=http://channel-service:8004 \
  frontend-service
```

## ⚙️ Environment Configuration

### Required Environment Variables
```env
# Backend Service URLs
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8001
NEXT_PUBLIC_CREATOR_HUB_SERVICE_URL=http://localhost:8002  
NEXT_PUBLIC_AI_ENGINE_SERVICE_URL=http://localhost:8003
NEXT_PUBLIC_CHANNEL_SERVICE_URL=http://localhost:8004

# Development Configuration
NEXT_PUBLIC_ENABLE_DEV_ROUTES=true
NEXT_PUBLIC_DEBUG_MODE=true

# API Configuration  
NEXT_PUBLIC_API_TIMEOUT=10000
NEXT_PUBLIC_AUTOSAVE_INTERVAL=30000
NEXT_PUBLIC_MAX_NODES_PER_PROGRAM=50

# Frontend Port
PORT=8006
```

## 🔐 Access Control

### Development Access Codes
- `dev2025`
- `coaching-ai-dev`
- `visual-program-builder`

### Route Protection
- **Development routes** (`/testing`) are protected by authentication
- **Environment-based access** control (dev mode must be enabled)
- **Session-based authentication** with automatic logout

## 🎨 Visual Program Builder Usage

### Creating Programs
1. **Access the testing interface** with development credentials
2. **Drag nodes** from the toolbar to the canvas
3. **Connect nodes** using the handles to create program flow
4. **Configure each step** using the sidebar panel
5. **Validate the program** using the built-in validation panel
6. **Save automatically** or manually trigger saves

### Node Types Available
- **💬 Message**: Send messages to users with AI enhancement
- **✅ Task**: Assign tasks with tracking and completion
- **📋 Survey**: Collect user feedback and responses
- **⏱️ Wait**: Pause program execution for specified duration
- **🔀 Condition**: Create conditional logic branches
- **⚡ Trigger**: Define program start points and triggers

### AI Integration Features
- **Knowledge Context**: Use creator's uploaded documents
- **Personality Enhancement**: Apply creator's coaching style
- **Dynamic Prompts**: Generate personalized content
- **Real-time Validation**: Ensure program integrity

## 🧪 Testing Interface Features

### Program Validation
- **Real-time error checking** with detailed error messages
- **Performance warnings** for complex programs
- **Integration validation** for AI features
- **Flow analysis** for orphaned or dead-end nodes

### Debugging Tools
- **Step execution tracing** with detailed logs
- **Connection visualization** showing program flow
- **Performance monitoring** with execution times
- **Export/Import functionality** for program sharing

## 📊 Integration Status

### Backend Service Integration
- ✅ **Auth Service (8001)**: Complete authentication integration
- ✅ **Creator Hub Service (8002)**: Full program management API
- ✅ **AI Engine Service (8003)**: Knowledge and AI features
- ✅ **Channel Service (8004)**: Multi-channel deployment support

### API Coverage
- ✅ **Authentication**: Login, register, token refresh, logout
- ✅ **Program Management**: CRUD operations, step management
- ✅ **Knowledge Management**: Document upload, search, processing
- ✅ **Personality System**: Analysis, prompt generation, monitoring
- ✅ **Program Execution**: Testing, validation, analytics

## 🚀 Production Readiness

### Performance Optimizations
- **React Flow virtualization** for large programs
- **Zustand optimized selectors** for minimal re-renders
- **API request caching** with automatic invalidation
- **Optimistic updates** for responsive UI

### Security Features
- **JWT-based authentication** with automatic refresh
- **Environment-based route protection**
- **XSS protection** via Next.js built-in security
- **CORS handling** through API proxy configuration

### Monitoring & Analytics
- **Real-time validation feedback**
- **API error tracking and reporting** 
- **Performance metrics collection**
- **User interaction analytics**

## 🔮 Future Development

### Immediate Enhancements
- **Enhanced node types** for advanced program logic
- **Collaboration features** for team-based program building
- **Template library** for quick program creation
- **Advanced analytics dashboard**

### Long-term Vision
- **Creator-facing frontend** for end-user program building
- **Mobile responsiveness** for tablet-based editing
- **Real-time collaboration** with WebSocket integration
- **Marketplace integration** for program sharing

---

**Status**: ✅ **PRODUCTION READY**  
**Integration**: Complete with all backend services  
**Purpose**: Internal testing and development interface  
**Technology**: Next.js 15 + React Flow + TypeScript  
**Port**: 8006

This Frontend Service serves as both an immediate testing tool for the development team and the foundation for the future creator-facing visual program builder interface.