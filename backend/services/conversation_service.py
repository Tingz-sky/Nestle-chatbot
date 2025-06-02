import logging
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

logger = logging.getLogger(__name__)

class InMemoryChatMessageHistory(BaseChatMessageHistory):
    """
    Simple in-memory implementation of chat message history.
    """
    
    def __init__(self):
        self.messages = []
    
    def add_message(self, message):
        self.messages.append(message)
    
    def clear(self):
        self.messages = []

class ConversationService:
    """
    Service to manage conversation memory and context for multi-turn dialogue
    using LangChain's updated memory components
    """
    
    def __init__(self):
        # Dictionary to store conversation memories by session ID
        self.sessions: Dict[str, InMemoryChatMessageHistory] = {}
        logger.info("Initialized ConversationService")
    
    def get_or_create_memory(self, session_id: str) -> InMemoryChatMessageHistory:
        """
        Get an existing conversation memory or create a new one for the session
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            InMemoryChatMessageHistory: The memory object for this session
        """
        if session_id not in self.sessions:
            logger.info(f"Creating new conversation memory for session: {session_id}")
            self.sessions[session_id] = InMemoryChatMessageHistory()
        
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, message_type: str, content: str) -> None:
        """
        Add a message to the conversation history with different types
        
        Args:
            session_id: Session ID
            message_type: Message type ('user'/'ai'/'system')
            content: Message content
        """
        memory = self.get_or_create_memory(session_id)
        
        if message_type == "user":
            memory.add_message(HumanMessage(content=content))
            logger.debug(f"Added user message to session {session_id}")
        elif message_type == "ai":
            memory.add_message(AIMessage(content=content))
            logger.debug(f"Added AI message to session {session_id}")
        elif message_type == "system":
            memory.add_message(SystemMessage(content=content))
            logger.debug(f"Added system message to session {session_id}")
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    def add_user_message(self, session_id: str, message: str) -> None:
        """
        Add a user message to the conversation history
        
        Args:
            session_id: Unique identifier for the conversation session
            message: The user's message text
        """
        self.add_message(session_id, "user", message)
    
    def add_ai_message(self, session_id: str, message: str) -> None:
        """
        Add an AI response to the conversation history
        
        Args:
            session_id: Unique identifier for the conversation session
            message: The AI's response text
        """
        self.add_message(session_id, "ai", message)
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the full conversation history for a session
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            List of conversation messages as dictionaries with 'type' and 'content' keys
        """
        memory = self.get_or_create_memory(session_id)
        messages = memory.messages
        
        # Convert LangChain message objects to dictionaries
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"type": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"type": "ai", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                history.append({"type": "system", "content": msg.content})
        
        return history
    
    def get_memory_messages(self, session_id: str) -> List[Any]:
        """
        Get memory messages in the format expected by LangChain
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            List of message objects
        """
        memory = self.get_or_create_memory(session_id)
        return memory.messages
    
    def clear_memory(self, session_id: str) -> None:
        """
        Clear the conversation history for a session
        
        Args:
            session_id: Unique identifier for the conversation session
        """
        if session_id in self.sessions:
            logger.info(f"Clearing conversation memory for session: {session_id}")
            self.sessions[session_id].clear()
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete a conversation session completely
        
        Args:
            session_id: Unique identifier for the conversation session
        """
        if session_id in self.sessions:
            logger.info(f"Deleting conversation session: {session_id}")
            del self.sessions[session_id] 