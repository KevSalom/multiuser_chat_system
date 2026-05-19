import streamlit as st
from datetime import datetime
from memory_manager import ModernMemoryManager, UserManager
from chatbot import ChatbotManager
from utils import (
    format_timestamp,
    truncate_text,
    validate_user_id,
    get_memory_category_icon
)
from config import PAGE_TITLE, PAGE_ICON

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_chat' not in st.session_state:
        st.session_state.current_chat = None
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'memory_manager' not in st.session_state:
        st.session_state.memory_manager = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'show_memories' not in st.session_state:
        st.session_state.show_memories = False

def user_selection_sidebar():
    st.sidebar.header("👤 User")
    
    existing_users = UserManager.get_users()
    
    if existing_users:
        selected_user = st.sidebar.selectbox(
            "Select user:",
            [""] + existing_users,
            key="user_selector"
        )
        if selected_user and selected_user != st.session_state.current_user:
            st.session_state.current_user = selected_user
            st.session_state.chatbot = ChatbotManager.get_chatbot(selected_user)
            st.session_state.memory_manager = ModernMemoryManager(selected_user)
            st.session_state.current_chat = None
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.sidebar.info("No users created")
    
    with st.sidebar.expander("Create new user", expanded=not existing_users):
        new_user_id = st.text_input(
            "User ID:",
            placeholder="user123",
            help="Only letters, numbers, - and _",
            key="new_user_input"
        )
        if st.button("Create User", type="primary", key="create_user_btn"):
            if not new_user_id:
                st.error("Enter a user ID")
            elif not validate_user_id(new_user_id):
                st.error("Invalid ID. Only letters, numbers, - and _")
            elif UserManager.user_exists(new_user_id):
                st.error("User already exists")
            else:
                if UserManager.create_user(new_user_id):
                    st.session_state.current_user = new_user_id
                    st.session_state.chatbot = ChatbotManager.get_chatbot(new_user_id)
                    st.session_state.memory_manager = ModernMemoryManager(new_user_id)
                    st.session_state.current_chat = None
                    st.session_state.chat_history = []
                    st.success(f"User '{new_user_id}' created")
                    st.rerun()
                else:
                    st.error("Error creating user")

def chat_history_sidebar():
    if not st.session_state.current_user:
        return
    
    st.sidebar.header("💬 Chats")
    memory_manager = st.session_state.memory_manager
    
    if st.sidebar.button("➕ New Chat", type="primary", use_container_width=True):
        new_chat_id = memory_manager.create_new_chat()
        st.session_state.current_chat = new_chat_id
        st.session_state.chat_history = []
        st.rerun()
    
    st.sidebar.markdown("---")
    
    chats = memory_manager.get_user_chats()
    if chats:
        st.sidebar.subheader("History")
        for chat in chats:
            chat_id = chat['chat_id']
            title = chat['title']
            message_count = chat.get('message_count', 0)
            updated_at = format_timestamp(chat['updated_at'])
            
            chat_container = st.sidebar.container()
            with chat_container:
                col1, col2 = st.columns([4, 1])
                with col1:
                    is_active = st.session_state.current_chat == chat_id
                    button_args = {
                        "label": f"💬 {truncate_text(title, 25)}",
                        "key": f"chat_{chat_id}",
                        "help": f"Messages: {message_count} | Updated: {updated_at}",
                        "use_container_width": True
                    }
                    if is_active:
                        button_args["type"] = "secondary"
                    if st.button(**button_args):
                        if st.session_state.current_chat != chat_id:
                            st.session_state.current_chat = chat_id
                            st.session_state.chat_history = st.session_state.chatbot.get_conversation_history(chat_id)
                            st.rerun()
                with col2:
                    if st.button(
                        "🗑️",
                        key=f"delete_{chat_id}",
                        help="Delete chat"
                    ):
                        if memory_manager.delete_chat(chat_id):
                            if st.session_state.chatbot:
                                st.session_state.chatbot.delete_chat_from_langgraph(chat_id)
                            if st.session_state.current_chat == chat_id:
                                st.session_state.current_chat = None
                                st.session_state.chat_history = []
                            st.rerun()
        
        st.sidebar.markdown(f"**Total chats:** {len(chats)}")
    else:
        st.sidebar.info("No chats yet.\nClick 'New Chat' to start.")

def main_chat_interface():
    if not st.session_state.current_user:
        st.title(PAGE_TITLE)
        st.info("👈 Select or create a user in the sidebar to start")
        return
    
    chatbot = st.session_state.chatbot
    if not chatbot:
        st.error("Error initializing chatbot")
        return
    
    if not st.session_state.current_chat:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.title("🤖 AI Assistant")
            st.markdown(f"**Hello, {st.session_state.current_user}!**")
            st.markdown("How can I help you today?")
            st.markdown("### You can ask me about:")
            st.markdown("""
            - 💼 **Work and projects**
            - 📚 **Learn something new**
            - 🤔 **Solve problems**
            - 💡 **Creative ideas**
            - 📋 **Planning and tasks**
            """)
            st.markdown("</div>", unsafe_allow_html=True)
        
        user_input = st.chat_input("Start a new conversation...")
        if user_input:
            memory_manager = st.session_state.memory_manager
            new_chat_id = memory_manager.create_new_chat(user_input)
            st.session_state.current_chat = new_chat_id
            process_user_message(user_input)
        return
    
    current_chat_info = st.session_state.memory_manager.get_chat_info(st.session_state.current_chat)
    if not current_chat_info:
        st.error("Chat not found")
        return
    
    st.title(f"💬 {current_chat_info['title']}")
    st.caption(f"User: {st.session_state.current_user}")
    
    if not st.session_state.chat_history:
        st.session_state.chat_history = chatbot.get_conversation_history(st.session_state.current_chat)
    
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                timestamp = format_timestamp(message.get('timestamp', ''))
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(message['content'])
                        if timestamp:
                            st.caption(f"📅 {timestamp}")
                else:
                    with st.chat_message("assistant"):
                        st.write(message['content'])
                        if timestamp:
                            st.caption(f"📅 {timestamp}")
        else:
            st.info("Start the conversation by typing a message.")
    
    user_input = st.chat_input("Type your message here...")
    if user_input:
        process_user_message(user_input)

def process_user_message(user_input: str):
    with st.chat_message("user"):
        st.write(user_input)
        st.caption(f"📅 {format_timestamp(datetime.now().isoformat())}")
    
    with st.spinner("Thinking..."):
        response = st.session_state.chatbot.chat(user_input, st.session_state.current_chat)
    
    if response['success']:
        with st.chat_message("assistant"):
            st.write(response['response'])
            caption_parts = [f"📅 {format_timestamp(datetime.now().isoformat())}"]
            if response.get('memories_used', 0) > 0:
                caption_parts.append(f"🧠 {response['memories_used']} memories")
            if response.get('context_optimized'):
                caption_parts.append("⚡ Optimized")
            st.caption(" | ".join(caption_parts))
        
        st.session_state.memory_manager.update_chat_metadata(
            st.session_state.current_chat,
            increment_messages=True
        )
        
        st.session_state.chat_history = st.session_state.chatbot.get_conversation_history(
            st.session_state.current_chat
        )
        st.rerun()
    else:
        st.error(f"Error: {response['error']}")

def show_memory_interface(container=st):
    container.subheader("🧠 Vector Memory")
    if container.button("Close", key="close_memories"):
        st.session_state.show_memories = False
        st.rerun()
    if not st.session_state.memory_manager:
        container.error("No memory manager available")
        return
    
    memories = st.session_state.memory_manager.get_all_vector_memories()
    if not memories:
        container.info("No memories saved yet. The system will automatically save important information from your conversations.")
        return
    
    col1, col2, col3 = container.columns(3)
    with col1:
        st.metric("Total Memories", len(memories))
    with col2:
        categories = [mem['metadata'].get('category', 'no_category') for mem in memories]
        unique_categories = len(set(categories))
        st.metric("Categories", unique_categories)
    with col3:
        high_importance = sum(1 for mem in memories if mem['metadata'].get('importance', 0) >= 4)
        st.metric("High Importance", high_importance)
    
    categories = list(set(mem['metadata'].get('category', 'no_category') for mem in memories))
    selected_category = container.selectbox(
        "Filter by category:",
        ["All"] + sorted(categories)
    )
    
    filtered_memories = memories
    if selected_category != "All":
        filtered_memories = [
            mem for mem in memories
            if mem['metadata'].get('category') == selected_category
        ]
    
    filtered_memories.sort(
        key=lambda x: (
            x['metadata'].get('importance', 0),
            x['metadata'].get('timestamp', '')
        ),
        reverse=True
    )
    
    container.write(f"Showing {len(filtered_memories)} of {len(memories)} memories")
    for memory in filtered_memories:
        category = memory['metadata'].get('category', 'no_category')
        timestamp = memory['metadata'].get('timestamp', '')
        importance = memory['metadata'].get('importance', 0)
        
        title_parts = [get_memory_category_icon(category)]
        title_parts.append(truncate_text(memory['content'], 60))
        if importance > 0:
            title_parts.append(f"({'⭐' * importance})")
        title = " ".join(title_parts)
        
        with container.expander(title, expanded=False):
            st.write(memory['content'])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"**Category:** {category}")
            with col2:
                if importance > 0:
                    st.caption(f"**Importance:** {'⭐' * importance}")
            with col3:
                st.caption(f"**Date:** {format_timestamp(timestamp)}")

def main():
    init_session_state()
    
    user_selection_sidebar()
    
    if st.session_state.current_user:
        chat_history_sidebar()
        
        st.sidebar.markdown("---")
        st.sidebar.info(f"**User:** {st.session_state.current_user}")
        
        if st.sidebar.button("🧠 View All Memories", use_container_width=True):
            st.session_state.show_memories = True
    
    if st.session_state.show_memories:
        chat_col, mem_col = st.columns([3, 2])
        with chat_col:
            main_chat_interface()
        with mem_col:
            show_memory_interface(container=mem_col)
    else:
        main_chat_interface()

if __name__ == "__main__":
    main()