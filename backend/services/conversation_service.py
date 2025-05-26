import logging
from typing import Dict, List, Any, Optional
import time

logger = logging.getLogger(__name__)

class Message:
    """
    Represents a single message in a conversation
    """
    def __init__(self, content: str, is_user: bool, timestamp: float = None):
        self.content = content
        self.is_user = is_user  # True for user messages, False for AI messages
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format"""
        return {
            "type": "human" if self.is_user else "ai",
            "content": self.content,
            "timestamp": self.timestamp
        }

class ConversationMemory:
    """
    Stores conversation history for a session
    """
    def __init__(self):
        self.messages: List[Message] = []
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the history"""
        self.messages.append(Message(content=content, is_user=True))
    
    def add_ai_message(self, content: str) -> None:
        """Add an AI message to the history"""
        self.messages.append(Message(content=content, is_user=False))
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in dictionary format"""
        return [msg.to_dict() for msg in self.messages]
    
    def clear(self) -> None:
        """Clear all messages"""
        self.messages = []

class ConversationService:
    """
    Service to manage conversation memory and context for multi-turn dialogue
    """
    
    def __init__(self):
        # Dictionary to store conversation memories by session ID
        self.sessions: Dict[str, ConversationMemory] = {}
        logger.info("Initialized ConversationService")
    
    def get_or_create_memory(self, session_id: str) -> ConversationMemory:
        """
        Get an existing conversation memory or create a new one for the session
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            ConversationMemory: The memory object for this session
        """
        if session_id not in self.sessions:
            logger.info(f"Creating new conversation memory for session: {session_id}")
            self.sessions[session_id] = ConversationMemory()
        
        return self.sessions[session_id]
    
    def add_user_message(self, session_id: str, message: str) -> None:
        """
        Add a user message to the conversation history
        
        Args:
            session_id: Unique identifier for the conversation session
            message: The user's message text
        """
        memory = self.get_or_create_memory(session_id)
        memory.add_user_message(message)
        logger.debug(f"Added user message to session {session_id}")
    
    def add_ai_message(self, session_id: str, message: str) -> None:
        """
        Add an AI response to the conversation history
        
        Args:
            session_id: Unique identifier for the conversation session
            message: The AI's response text
        """
        memory = self.get_or_create_memory(session_id)
        memory.add_ai_message(message)
        logger.debug(f"Added AI message to session {session_id}")
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the full conversation history for a session
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            List of conversation messages as dictionaries with 'type' and 'content' keys
        """
        memory = self.get_or_create_memory(session_id)
        return memory.get_messages()
    
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