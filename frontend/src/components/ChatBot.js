import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

// Chat UI Components
const ChatContainer = styled.div`
  width: ${props => props.isExpanded ? '500px' : '400px'};
  height: ${props => props.isExpanded ? '600px' : '500px'};
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.3s ease, opacity 0.3s ease, height 0.3s ease, width 0.3s ease;
  transform: ${props => props.isOpen ? 'scale(1)' : 'scale(0.9)'};
  opacity: ${props => props.isOpen ? 1 : 0};
  pointer-events: ${props => props.isOpen ? 'all' : 'none'};
  position: relative;
`;

const ChatHeader = styled.div`
  background-color: #007a33;
  color: white;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ChatTitle = styled.div`
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const BotLogo = styled.div`
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  
  & img {
    width: 24px;
    height: 24px;
  }
`;

const IconButton = styled.button`
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
  
  &:hover {
    opacity: 0.8;
  }
`;

const HeaderButtons = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
`;

const ExpandButton = styled.button`
  background: none;
  border: none;
  color: white;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    opacity: 0.8;
  }
`;

const ChatMessages = styled.div`
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const Message = styled.div`
  max-width: 85%;
  padding: 12px 15px;
  border-radius: 18px;
  margin-bottom: 5px;
  font-size: 14px;
  line-height: 1.4;
  position: relative;
  
  ${props => props.isBot ? `
    align-self: flex-start;
    background-color: #f0f2f5;
    color: #1c1e21;
    border-bottom-left-radius: 5px;
  ` : `
    align-self: flex-end;
    background-color: #007a33;
    color: white;
    border-bottom-right-radius: 5px;
  `}
  
  & p {
    margin: 0 0 10px 0;
  }
  
  & p:last-child {
    margin-bottom: 0;
  }
  
  & ul, & ol {
    margin: 0;
    padding-left: 20px;
  }
  
  & a {
    color: ${props => props.isBot ? '#007a33' : 'white'};
    text-decoration: underline;
  }
  
  & code {
    font-family: monospace;
    background-color: ${props => props.isBot ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.15)'};
    padding: 2px 4px;
    border-radius: 3px;
  }
  
  & pre {
    background-color: ${props => props.isBot ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.15)'};
    padding: 8px;
    border-radius: 5px;
    overflow-x: auto;
    margin: 10px 0;
  }
`;

const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  margin-top: 5px;
  gap: 3px;
  
  span {
    width: 6px;
    height: 6px;
    background-color: #007a33;
    border-radius: 50%;
    display: inline-block;
    animation: bounce 1.3s infinite ease-in-out;
    
    &:nth-child(1) {
      animation-delay: 0s;
    }
    
    &:nth-child(2) {
      animation-delay: 0.15s;
    }
    
    &:nth-child(3) {
      animation-delay: 0.3s;
    }
  }
  
  @keyframes bounce {
    0%, 60%, 100% {
      transform: translateY(0);
    }
    30% {
      transform: translateY(-4px);
    }
  }
`;

const MessageContent = styled.div`
  white-space: pre-wrap;
`;

const References = styled.div`
  margin-top: 8px;
  font-size: 12px;
  
  a {
    color: var(--secondary-color);
    text-decoration: none;
    display: block;
    margin-top: 4px;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

const ChatInputContainer = styled.div`
  display: flex;
  padding: 15px;
  border-top: 1px solid #e0e0e0;
  align-items: center;
`;

const ChatInput = styled.input`
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: 10px 15px;
  outline: none;
  font-size: 14px;
  
  &:focus {
    border-color: var(--primary-color);
  }
`;

const SendButton = styled.button`
  background-color: #007a33;
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  margin-left: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #005522;
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const ChatBubble = styled.div`
  width: 60px;
  height: 60px;
  background-color: #007a33;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s;
  
  &:hover {
    transform: scale(1.05);
  }
  
  & img {
    width: 35px;
    height: 35px;
  }
`;

const ResizeControls = styled.div`
  position: absolute;
  right: 10px;
  bottom: 75px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  z-index: 100;
`;

const ResizeButton = styled.button`
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: rgba(0, 122, 51, 0.1);
  border: 1px solid rgba(0, 122, 51, 0.2);
  color: #007a33;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  
  &:hover {
    background-color: rgba(0, 122, 51, 0.2);
  }
`;

// Main component
const ChatBot = ({ isOpen, toggleChat }) => {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: "Welcome to Nestle Assistant! I can provide information about Nestle products, nutrition facts, recipes, and sustainability initiatives. What would you like to learn about today?", 
      isBot: true
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [fontSize, setFontSize] = useState(14);
  
  const messagesEndRef = useRef(null);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
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
    
    // 添加"正在输入"的占位消息
    const loadingMessageId = messages.length + 2;
    const loadingMessage = {
      id: loadingMessageId,
      text: '',
      isBot: true,
      isLoading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);
    scrollToBottom();
    
    try {
      // Call API
      const response = await axios.post('/api/chat', {
        query: input,
        session_id: sessionId
      });
      
      // Store session ID
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }
      
      // 移除加载消息，添加实际响应
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
      
      // Add bot response
      const botMessage = {
        id: loadingMessageId,
        text: response.data.response,
        isBot: true,
        references: response.data.references || []
      };
      
      setMessages(prev => [...prev, botMessage]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      // 移除加载消息
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
      
      // Add error message
      const errorMessage = {
        id: loadingMessageId,
        text: "Sorry, I'm having trouble connecting. Please try again later.",
        isBot: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const increaseFontSize = () => {
    if (fontSize < 18) {
      setFontSize(fontSize + 1);
    }
  };

  const decreaseFontSize = () => {
    if (fontSize > 12) {
      setFontSize(fontSize - 1);
    }
  };
  
  return (
    <>
      {isOpen ? (
        <ChatContainer isOpen={isOpen} isExpanded={isExpanded}>
          <ChatHeader>
            <ChatTitle>
              <BotLogo>
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABPUlEQVR4nO2UQUoDQRBFf8AbeILewZV4Bj2BnsAzeAIXiSvBnXsXLj2JbhWCiOAiMZJAQB2NYQgkGaebyWQSXEigl9MNP/+v6uluhl2CTS8pgGPgHJgCH8A3sACegDtgCPTqkg+BG+CTv/ENPAIDYKcq+QnwXJJ0CVwCZ8ARcABcAFPL+wLGbvO6jbsEoydgOLcbYyPOj4FrYG7nvhyfF8Y+qEoedDZlV11W4Aa4j/ik/N9yrJzEqk0wLvmYbeQF2I8k2v9DFfJAMimRHBQEF1XJeybpcjORZBfr2qZtLPKl/m4wGW9q0TISA2NnS+M/qvt3tM0UXUbO32kUKDnbrhrZX9tbRUW5Bfo22Trrqm3cNDXUxp32YukS+PIM3iXNzGcunaSXuTZ5xvoDMk/I2qzb8c8C9QEP5ZJ/AV09WAAAAABJRU5ErkJggg==" alt="Bot" />
              </BotLogo>
              SMARTIE
            </ChatTitle>
            <HeaderButtons>
              <ExpandButton onClick={toggleExpand} title={isExpanded ? "Compact view" : "Expanded view"}>
                {isExpanded ? "⊟" : "⊞"}
              </ExpandButton>
              <IconButton onClick={toggleChat}>×</IconButton>
            </HeaderButtons>
          </ChatHeader>
          
          <ChatMessages>
            {messages.map((message, index) => (
              <Message 
                key={message.id} 
                isBot={message.isBot}
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
          
          <ResizeControls>
            <ResizeButton onClick={increaseFontSize} title="Increase font size">
              A+
            </ResizeButton>
            <ResizeButton onClick={decreaseFontSize} title="Decrease font size">
              A-
            </ResizeButton>
          </ResizeControls>
          
          <ChatInputContainer>
            <ChatInput
              type="text"
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              style={{ fontSize: `${fontSize}px` }}
            />
            <SendButton onClick={handleSendMessage} disabled={isLoading || !input.trim()}>
              {isLoading ? "" : "➤"}
            </SendButton>
          </ChatInputContainer>
        </ChatContainer>
      ) : (
        <ChatBubble onClick={toggleChat}>
          <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABPUlEQVR4nO2UQUoDQRBFf8AbeILewZV4Bj2BnsAzeAIXiSvBnXsXLj2JbhWCiOAiMZJAQB2NYQgkGaebyWQSXEigl9MNP/+v6uluhl2CTS8pgGPgHJgCH8A3sACegDtgCPTqkg+BG+CTv/ENPAIDYKcq+QnwXJJ0CVwCZ8ARcABcAFPL+wLGbvO6jbsEoydgOLcbYyPOj4FrYG7nvhyfF8Y+qEoedDZlV11W4Aa4j/ik/N9yrJzEqk0wLvmYbeQF2I8k2v9DFfJAMimRHBQEF1XJeybpcjORZBfr2qZtLPKl/m4wGW9q0TISA2NnS+M/qvt3tM0UXUbO32kUKDnbrhrZX9tbRUW5Bfo22Trrqm3cNDXUxp32YukS+PIM3iXNzGcunaSXuTZ5xvoDMk/I2qzb8c8C9QEP5ZJ/AV09WAAAAABJRU5ErkJggg==" alt="Chat" />
        </ChatBubble>
      )}
    </>
  );
};

export default ChatBot; 