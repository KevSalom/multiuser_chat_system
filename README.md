# Chat Multi-Usuario con Memoria Avanzada

Sistema de chat multi-usuario con memoria vectorial persistente usando LangGraph y ChromaDB.

## Descripción

Chat multi-usuario inteligente que utiliza:
- **LangGraph** para orquestar mensajes y memoria
- **ChromaDB** para memoria vectorial persistente por usuario
- **Multi-usuario** con gestión de chats independientes
- **Extracción automática** de memorias importantes
- **Optimización de contexto** con trim_messages

## Arquitectura

```
Usuario → Chat → LangGraph → Memory Retrieval
                            → Context Optimization
                            → Response Generation
                            → Memory Extraction → ChromaDB
```

## Técnicas Utilizadas

### 1. Gestión de Memoria Vectorial
- ChromaDB por usuario
- Extracción inteligente de memorias via LLM
- Búsqueda semántica de memorias relevantes
- Categorización (personal, profesional, preferencias, hechos_importantes)

### 2. LangGraph con Estado Persistente
- SQLite checkpointer para persistencia
- Thread por chat (user_id + chat_id)
- trim_messages para gestión de contexto
- Flujo secuencial: retrieval → optimization → response → extraction

### 3. Sistema Multi-Usuario
- Gestión de usuarios con UserManager
- Chats independientes por usuario
- Metadatos de chat en JSON ligero
- Historial de conversación persistente

## Estructura del Proyecto

```
multiuser_chat_system/
├── app.py              # Aplicación Streamlit
├── chatbot.py          # ModernChatbot con LangGraph
├── memory_manager.py   # Gestión de memoria vectorial
├── config.py           # Configuración
├── utils.py            # Utilidades auxiliares
├── users/              # Datos de usuarios (git ignored)
└── data/               # Datos adicionales (git ignored)
```

## Requisitos

- Python 3.10+
- OpenAI API Key

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Crear archivo `.env` con tu API key:

```
OPENAI_API_KEY=sk-your-key-here
```

## Uso

1. **Iniciar la aplicación:**
```bash
streamlit run app.py
```

2. **Crear usuario:**
   - Sidebar: escribir ID de usuario
   - Click "Crear Usuario"

3. **Crear nuevo chat:**
   - Click "Nuevo Chat"
   - Escribir mensaje para iniciar

4. **Ver memorias:**
   - Click "Ver Todas las Memorias"
   - Filtrar por categoría
   - Ver contenido e importancia

## Funcionalidades

- 💬 Chats independientes por conversación
- 🧠 Memoria vectorial persistente
- 🔍 Búsqueda de memorias pasadas
- ⭐ Importancia de memorias (1-5)
- 📝 Extracción automática de información importante
- 👤 Multi-usuario con datos aislados