import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import ApiService from '../services/apiService';
import { 
  ChatContainer, ChatHeader, ChatTitle, BotLogo, 
  HeaderButtons, ExpandButton, IconButton, ChatMessages, 
  Message, TypingIndicator, References, ChatInputContainer, 
  ChatInput, SendButton, ChatBubble, ResizeControls, ResizeButton 
} from './ChatStyles';
import styled from 'styled-components';

// Constants
const MAX_RETRY_ATTEMPTS = 2;
const INITIAL_MESSAGE = {
  id: 1, 
  text: "Welcome to NesBot! I can provide information about Nestle products, nutrition facts, recipes, and sustainability initiatives. What would you like to learn about today?", 
  isBot: true
};

// Add a new ClearButton style component
const ClearButton = styled(ResizeButton)`
  margin-right: 10px;
  background-color: #f2f2f2;
  font-size: ${props => props.isExpanded ? '13px' : '11px'};
  width: ${props => props.isExpanded ? '36px' : '30px'};
  height: ${props => props.isExpanded ? '36px' : '30px'};
  &:hover {
    background-color: #e0e0e0;
  }
`;

/**
 * ChatBot component that provides the interface for user interaction
 * @param {Object} props - Component props
 * @param {boolean} props.isOpen - Whether the chat window is open
 * @param {function} props.toggleChat - Function to toggle chat open/closed
 */
const ChatBot = ({ isOpen, toggleChat }) => {
  // State management
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [fontSize, setFontSize] = useState(14);
  
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  /**
   * Scrolls chat to the bottom
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  /**
   * Handles sending user message and getting response from API
   */
  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    // Add user message
    const userMessage = {
      id: messages.length + 1,
      text: input,
      isBot: false
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    // Add typing indicator placeholder message
    const loadingMessageId = messages.length + 2;
    const loadingMessage = {
      id: loadingMessageId,
      text: '',
      isBot: true,
      isLoading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);
    scrollToBottom();
    
    let retryCount = 0;
    
    while (retryCount <= MAX_RETRY_ATTEMPTS) {
      try {
        // Use API service to send message
        const response = await ApiService.sendChatMessage(input, sessionId);
        
        // Store session ID
        if (response.data.session_id) {
          setSessionId(response.data.session_id);
        }
        
        // Remove loading message
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
        
        // Add bot response
        const botMessage = {
          id: loadingMessageId,
          text: response.data.response,
          isBot: true,
          references: response.data.references || []
        };
        
        setMessages(prev => [...prev, botMessage]);
        
        // Success - break out of retry loop
        break;
        
      } catch (error) {
        console.error('Error sending message:', error);
        
        if (retryCount < MAX_RETRY_ATTEMPTS) {
          // Wait before retry (exponential backoff)
          // Use a closure to capture the current value of retryCount
          const currentRetryCount = retryCount;
          await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, currentRetryCount)));
          retryCount++;
        } else {
          // Remove loading message after all retries failed
          setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
          
          // Determine error message based on error type
          let errorMessage = "Sorry, I'm having trouble connecting. Please try again later.";
          
          if (error.response) {
            // Server responded with an error status code
            if (error.response.status === 500) {
              errorMessage = "Sorry, the server encountered an error. Our team is working on it.";
            } else if (error.response.status === 404) {
              errorMessage = "Sorry, the chatbot service couldn't be reached. Please try again later.";
            }
          } else if (error.request) {
            // Request was made but no response received (network error)
            errorMessage = "Network error. Please check your internet connection and try again.";
          }
          
          // Add error message
          const errorMessageObj = {
            id: loadingMessageId,
            text: errorMessage,
            isBot: true
          };
          
          setMessages(prev => [...prev, errorMessageObj]);
          break;
        }
      }
    }
    
    setIsLoading(false);
  };
  
  /**
   * Handles Enter key press in the chat input
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  /**
   * Toggles expanded/compact view
   */
  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  /**
   * Increases font size for better readability
   */
  const increaseFontSize = () => {
    const maxFontSize = isExpanded ? 22 : 18;
    if (fontSize < maxFontSize) {
      setFontSize(fontSize + 1);
    }
  };

  /**
   * Decreases font size
   */
  const decreaseFontSize = () => {
    const minFontSize = 12;
    if (fontSize > minFontSize) {
      setFontSize(fontSize - 1);
    }
  };
  
  /**
   * Clears the conversation history
   */
  const handleClearConversation = async () => {
    if (!sessionId) return;
    
    try {
      await ApiService.clearConversation(sessionId);
      
      // Reset chat to initial state
      setMessages([INITIAL_MESSAGE]);
      
      // Show a confirmation message
      const confirmationMessage = {
        id: 2,
        text: "Conversation history has been cleared. How can I help you today?",
        isBot: true
      };
      
      setMessages([INITIAL_MESSAGE, confirmationMessage]);
    } catch (error) {
      console.error('Error clearing conversation:', error);
      
      // Show error message
      const errorMessage = {
        id: messages.length + 1,
        text: "I couldn't clear the conversation history. Please try again later.",
        isBot: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };
  
  // Render chat interface or bubble based on isOpen state
  return (
    <>
      {isOpen ? (
        <ChatContainer isOpen={isOpen} isExpanded={isExpanded}>
          <ChatHeader>
            <ChatTitle>
              <BotLogo>
                <img src="/images/nestlechatboticon.png" alt="Bot" />
              </BotLogo>
              NesBot
            </ChatTitle>
            <HeaderButtons>
              <ExpandButton onClick={toggleExpand} title={isExpanded ? "Compact view" : "Expanded view"}>
                {isExpanded ? "⊟" : "⊞"}
              </ExpandButton>
              <IconButton onClick={toggleChat}>×</IconButton>
            </HeaderButtons>
          </ChatHeader>
          
          <ChatMessages isExpanded={isExpanded}>
            {messages.map((message, index) => (
              <Message 
                key={message.id} 
                isBot={message.isBot}
                isExpanded={isExpanded}
                className="message-enter"
                style={{ 
                  animationDelay: `${index * 0.1}s`,
                  fontSize: `${fontSize}px`
                }}
              >
                {message.isLoading ? (
                  <TypingIndicator>
                    <span></span>
                    <span></span>
                    <span></span>
                  </TypingIndicator>
                ) : (
                  <ReactMarkdown>
                    {message.text}
                  </ReactMarkdown>
                )}
                
                {message.isBot && message.references && message.references.length > 0 && (
                  <References style={{ fontSize: `${fontSize - 2}px` }}>
                    {message.references.map((ref, index) => (
                      <a key={index} href={ref.url} target="_blank" rel="noopener noreferrer">
                        {ref.title}
                      </a>
                    ))}
                  </References>
                )}
              </Message>
            ))}
            <div ref={messagesEndRef} />
          </ChatMessages>
          
          <ResizeControls isExpanded={isExpanded}>
            <ClearButton 
              isExpanded={isExpanded} 
              onClick={handleClearConversation}
              title="Clear conversation history"
            >
              Clear
            </ClearButton>
            <ResizeButton isExpanded={isExpanded} onClick={increaseFontSize} title="Increase font size">
              A+
            </ResizeButton>
            <ResizeButton isExpanded={isExpanded} onClick={decreaseFontSize} title="Decrease font size">
              A-
            </ResizeButton>
          </ResizeControls>
          
          <ChatInputContainer isExpanded={isExpanded}>
            <ChatInput
              isExpanded={isExpanded}
              type="text"
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              style={{ fontSize: `${fontSize}px` }}
            />
            <SendButton isExpanded={isExpanded} onClick={handleSendMessage} disabled={isLoading || !input.trim()}>
              {isLoading ? "" : "➤"}
            </SendButton>
          </ChatInputContainer>
        </ChatContainer>
      ) : (
        <ChatBubble onClick={toggleChat}>
          <img src="/images/nestlechatboticon.png" alt="Chat" />
        </ChatBubble>
      )}
    </>
  );
};

export default ChatBot; 