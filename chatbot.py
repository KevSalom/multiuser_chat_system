from langgraph.graph import StateGraph, START, END
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from memory_manager import ModernMemoryManager, MemoryState
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, OPENAI_API_KEY
import os

class ModernChatbot:

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_manager = ModernMemoryManager(user_id)

        self.llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
            api_key=OPENAI_API_KEY
        )

        self.system_template = """Eres un asistente personal inteligente y amigable.

Características de tu personalidad:
- Eres útil, empático y conversacional
- Recuerdas información importante de conversaciones anteriores
- Adaptas tu estilo a las preferencias del usuario
- Eres proactivo ofreciendo sugerencias relevantes
- Mantienes un tono profesional pero cercano

{context}

Usa esta información para personalizar tus respuestas, pero no menciones explícitamente que tienes memoria a menos que sea relevante para la conversación."""

        self.message_trimeer = trim_messages(
            strategy="last",
            max_tokens=4000,
            token_counter=self.llm,
            start_on="human",
            include_system=True
        )

        self.app = self._create_app()

    def _create_app(self):
        workflow = StateGraph(state_schema=MemoryState)

        def memory_retrieval_node(state):
            messages = state['messages']

            if not messages:
                return {"vector_memories": []}
            
            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg
                    break

            if not last_user_message:
                return {"vector_memories": []}
            
            relevant_memories = self.memory_manager.search_vector_memory(
                last_user_message.content
            )

            return {"vector_memories": relevant_memories}
        
        def context_optimization_node(state):
            messages = state['messages']

            trimmed_messages = self.message_trimeer.invoke(messages)

            return {"messages": trimmed_messages}
        
        def response_generation_node(state):
            messages = state['messages']
            vector_memories = state.get('vector_memories', [])

            if not messages:
                return {"messages": []}
            
            if vector_memories:
                context_parts = ["Informacion relevante que recuerdas del usuario:"]
                for memory in vector_memories:
                    context_parts.append(f"- {memory}")
                context = "\n".join(context_parts)
            else:
                context = "No hay informacion previa relevante disponible."

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_template.format(context=context)),
                MessagesPlaceholder(variable_name="messages")
            ])

            chain = prompt | self.llm
            response = chain.invoke({"messages": messages})

            return {"messages": response}

        def memory_extraction_node(state):
            messages = state['messages']
            last_extraction = state.get('last_memory_extraction')

            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg
                    break

            if not last_user_message:
                return {}
            
            if last_extraction != last_user_message.content:
                self.memory_manager.extract_and_store_memories(last_user_message.content)
                return {"last_memory_extraction": last_user_message.content}
            
            return {}
        
        workflow.add_node("memory_retrieval", memory_retrieval_node)
        workflow.add_node("context_optimization", context_optimization_node)
        workflow.add_node("response_generation", response_generation_node)
        workflow.add_node("memory_extraction", memory_extraction_node)

        workflow.add_edge(START, "memory_retrieval")
        workflow.add_edge("memory_retrieval", "context_optimization")
        workflow.add_edge("context_optimization", "response_generation")
        workflow.add_edge("response_generation", "memory_extraction")
        workflow.add_edge("memory_extraction", END)

        db_path = os.path.join(
            self.memory_manager.user_dir,
            "langgraph_memory.db"
        )

        conn = sqlite3.connect(db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)

        return workflow.compile(checkpointer=checkpointer)
    
    def chat(self, message: str, chat_id: str = "default"):
        try:
            config = {"configurable": {"thread_id": f"user_{self.user_id}_chat_{chat_id}"}}

            chat_info = self.memory_manager.get_chat_info(chat_id)
            if chat_info["title"] == "Nuevo chat":
                chat_title = self.memory_manager._generate_chat_title(message)
                self.memory_manager.update_chat_metadata(chat_id, chat_title)

            result = self.app.invoke(
                {"messages": [HumanMessage(content=message)]},
                config
            )

            assistant_response = result["messages"][-1].content

            return {
                "success": True,
                "response": assistant_response,
                "error": None,
                "memories_used": len(result.get("vector_memories", [])),
                "context_optimized": True
            }
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": str(e),
                "memories_used": 0,
                "context_optimized": False
            }
        
    def get_conversation_history(self, chat_id: str = "default", limit: int = 50):
        try:
            config = {"configurable": {"thread_id": f"user_{self.user_id}_chat_{chat_id}"}}

            state = self.app.get_state(config)

            if not state.values or "messages" not in state.values:
                return []
            
            messages = state.values["messages"]

            history = []
            for msg in messages[-limit:]:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    history.append({
                        'role': 'user' if isinstance(msg, HumanMessage) else 'assistant',
                        'content': msg.content,
                        'timestamp': getattr(msg, 'timestamp', None) or "2026-01-01T00:00:00"
                    })
            return history
        
        except Exception as e:
            print(f"Error obteniendo el historial: {e}")
            return []
        
    def clear_conversation(self, chat_id: str = "default") -> bool:
        try:
            config = {"configurable": {"thread_id": f"user_{self.user_id}_chat_{chat_id}"}}
            
            self.app.invoke({"messages": []}, config)
            return True
            
        except Exception as e:
            print(f"Error limpiando conversación: {e}")
            return False
    
    def delete_chat_from_langgraph(self, chat_id: str) -> bool:
        try:
            thread_id = f"user_{self.user_id}_chat_{chat_id}"
            
            config = {"configurable": {"thread_id": thread_id}}
            
            try:
                current_state = self.app.get_state(config)
                if not current_state.values:
                    return True
            except:
                return True
            
            return False
            
        except Exception as e:
            print(f"Error eliminando chat de LangGraph: {e}")
            return False
        

class ChatbotManager:

    _instances = {}

    @classmethod
    def get_chatbot(cls, user_id):
        if user_id not in cls._instances:
            cls._instances[user_id] = ModernChatbot(user_id)

        return cls._instances[user_id]
    
    @classmethod
    def remove_chatbot(cls, user_id):
        if user_id in cls._instances:
            del cls._instances[user_id]

    @classmethod
    def clear_all(cls):
        cls._instances.clear()