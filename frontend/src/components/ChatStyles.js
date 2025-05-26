import styled from 'styled-components';

// Primary color for the chatbot
const PRIMARY_COLOR = '#007a33';

export const ChatContainer = styled.div`
  width: ${props => props.isExpanded ? '600px' : '400px'};
  height: ${props => props.isExpanded ? '700px' : '500px'};
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
  margin: 10px;
`;

export const ChatHeader = styled.div`
  background-color: ${PRIMARY_COLOR};
  color: white;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

export const ChatTitle = styled.div`
  font-weight: 600;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
`;

export const BotLogo = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  
  & img {
    width: 32px;
    height: 32px;
    border-radius: 4px;
  }
`;

export const IconButton = styled.button`
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

export const HeaderButtons = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
`;

export const ExpandButton = styled.button`
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

export const ChatMessages = styled.div`
  flex: 1;
  padding: ${props => props.isExpanded ? '20px' : '15px'};
  padding-bottom: ${props => props.isExpanded ? '30px' : '25px'};
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: ${props => props.isExpanded ? '20px' : '15px'};
  background-color: #fafafa;
`;

export const Message = styled.div`
  max-width: 85%;
  padding: ${props => props.isExpanded ? '15px 18px' : '12px 15px'};
  border-radius: 18px;
  margin-bottom: 5px;
  font-size: ${props => props.isExpanded ? '16px' : '14px'};
  line-height: 1.5;
  position: relative;
  
  ${props => props.isBot ? `
    align-self: flex-start;
    background-color: #f0f2f5;
    color: #1c1e21;
    border-bottom-left-radius: 5px;
  ` : `
    align-self: flex-end;
    background-color: ${PRIMARY_COLOR};
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
    color: ${props => props.isBot ? PRIMARY_COLOR : 'white'};
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

export const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  margin-top: 5px;
  gap: 3px;
  
  span {
    width: 6px;
    height: 6px;
    background-color: ${PRIMARY_COLOR};
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

export const References = styled.div`
  margin-top: 8px;
  font-size: 12px;
  
  a {
    color: ${PRIMARY_COLOR};
    text-decoration: none;
    display: block;
    margin-top: 4px;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

export const ChatInputContainer = styled.div`
  display: flex;
  padding: ${props => props.isExpanded ? '20px' : '15px'};
  border-top: 1px solid #e0e0e0;
  align-items: center;
  background-color: white;
  border-radius: 0 0 10px 10px;
  margin-top: 2px;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.03);
`;

export const ChatInput = styled.input`
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: ${props => props.isExpanded ? '15px 20px' : '10px 15px'};
  outline: none;
  font-size: ${props => props.isExpanded ? '16px' : '14px'};
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  
  &:focus {
    border-color: ${PRIMARY_COLOR};
    box-shadow: 0 1px 5px rgba(0, 122, 51, 0.2);
  }
`;

export const SendButton = styled.button`
  background-color: ${PRIMARY_COLOR};
  color: white;
  border: none;
  border-radius: 50%;
  width: ${props => props.isExpanded ? '50px' : '40px'};
  height: ${props => props.isExpanded ? '50px' : '40px'};
  margin-left: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: ${props => props.isExpanded ? '20px' : '16px'};
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  
  &:hover {
    background-color: #005522;
    transform: scale(1.05);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

export const ChatBubble = styled.div`
  width: 90px;
  height: 90px;
  background-color: ${PRIMARY_COLOR};
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
    width: 80px;
    height: 80px;
    border-radius: 6px;
  }
`;

export const ResizeControls = styled.div`
  position: absolute;
  right: ${props => props.isExpanded ? '15px' : '10px'};
  bottom: ${props => props.isExpanded ? '95px' : '85px'};
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 100;
`;

export const ResizeButton = styled.button`
  width: ${props => props.isExpanded ? '34px' : '28px'};
  height: ${props => props.isExpanded ? '34px' : '28px'};
  border-radius: 50%;
  background-color: rgba(0, 122, 51, 0.1);
  border: 1px solid rgba(0, 122, 51, 0.2);
  color: ${PRIMARY_COLOR};
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: ${props => props.isExpanded ? '16px' : '14px'};
  transition: all 0.2s;
  
  &:hover {
    background-color: rgba(0, 122, 51, 0.2);
  }
`; 