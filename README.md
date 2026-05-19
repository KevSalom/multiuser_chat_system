# Multi-User Chat with Advanced Memory

Multi-user chat system with persistent vector memory using LangGraph and ChromaDB.

## Features

- 💬 **Multi-User Chats** - Independent conversations per user
- 🧠 **Vector Memory** - Persistent semantic memory per user
- 🔍 **Memory Search** - Search past memories and contexts
- ⭐ **Importance Scoring** - Memories rated 1-5 stars
- 📝 **Auto-Extraction** - Automatic extraction of important info
- 👤 **User Isolation** - Separate data per user
- 💾 **Persistent History** - Conversation history saved via LangGraph

## Description

Intelligent multi-user chat system that uses:
- **LangGraph** for orchestrating messages and memory
- **ChromaDB** for persistent per-user vector memory
- **Multi-user** with independent chat management
- **Automatic extraction** of important memories
- **Context optimization** with trim_messages

## Architecture

```
User → Chat → LangGraph → Memory Retrieval
                            → Context Optimization
                            → Response Generation
                            → Memory Extraction → ChromaDB
```

## Techniques Used

### 1. Vector Memory Management
- ChromaDB per user
- Intelligent memory extraction via LLM
- Semantic search of relevant memories
- Categorization (personal, professional, preferences, important_facts)

### 2. LangGraph with Persistent State
- SQLite checkpointer for persistence
- Thread per chat (user_id + chat_id)
- trim_messages for context management
- Sequential flow: retrieval → optimization → response → extraction

### 3. Multi-User System
- User management with UserManager
- Independent chats per user
- Lightweight chat metadata in JSON
- Persistent conversation history

## Project Structure

```
multiuser_chat_system/
├── app.py              # Streamlit application
├── chatbot.py          # ModernChatbot with LangGraph
├── memory_manager.py   # Vector memory management
├── config.py           # Configuration
├── utils.py            # Helper utilities
├── users/              # User data (git ignored)
├── data/               # Additional data (git ignored)
└── .env.example        # Environment template
```

## Requirements

- Python 3.10+
- OpenAI API Key

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```

## Usage

1. **Start the application:**
```bash
streamlit run app.py
```

2. **Create a user:**
   - Sidebar: enter user ID
   - Click "Create User"

3. **Create a new chat:**
   - Click "New Chat"
   - Write a message to start

4. **View memories:**
   - Click "View All Memories"
   - Filter by category
   - View content and importance