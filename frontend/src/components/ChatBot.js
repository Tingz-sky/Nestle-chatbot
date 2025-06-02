import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import ApiService from '../services/apiService';
import { 
  ChatContainer, ChatHeader, ChatTitle, BotLogo, 
  HeaderButtons, ExpandButton, IconButton, ChatMessages, 
  Message, TypingIndicator, References, ChatInputContainer, 
  ChatInput, SendButton, ChatBubble, ResizeControls, ResizeButton,
  ProductInfo, ProductTitle, PurchaseLink, StoresContainer,
  StoreItem, StoreHeader, StoreName, StoreDistance, StoreAddress,
  LocationButton
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
  font-size: ${props => props.isExpanded ? '0.8rem' : '0.65rem'};
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
  const [userLocation, setUserLocation] = useState(null);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  
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
   * Get user's geolocation and automatically fetch nearby stores
   */
  const getUserLocation = () => {
    if (!navigator.geolocation) {
      // Add a message if geolocation is not supported
      const message = {
        id: messages.length + 1,
        text: "Geolocation is not supported by your browser. I can't provide location-based store recommendations.",
        isBot: true,
        hasPurchaseIntent: true
      };
      
      setMessages(prev => [...prev, message]);
      return;
    }
    
    setIsGettingLocation(true);
    
    // Find the latest bot message to update (should be the current one)
    const latestBotMessageIndex = [...messages].reverse().findIndex(msg => msg.isBot && !msg.isLoading);
    if (latestBotMessageIndex === -1) {
      // If no bot message found, don't proceed
      setIsGettingLocation(false);
      return;
    }
    
    // Get the actual index in the original array
    const messageIndexToUpdate = messages.length - 1 - latestBotMessageIndex;
    const messageToUpdate = messages[messageIndexToUpdate];
    
    // Show loading state in the current message
    const updatedMessages = [...messages];
    updatedMessages[messageIndexToUpdate] = {
      ...messageToUpdate,
      text: messageToUpdate.text + "\n\nSearching for nearby stores...",
      isLoading: true,
      hasPurchaseIntent: true
    };
    setMessages(updatedMessages);
    
    navigator.geolocation.getCurrentPosition(
      // Success callback
      async (position) => {
        const location = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        
        setUserLocation(location);
        
        // Define standard product names for potential matches
        const productNames = [
          "KitKat", "Nescafé", "Smarties", "Nestea", "Perrier", 
          "San Pellegrino", "Coffee Crisp", "Aero", "Nestlé Pure Life", "MAGGI",
          "After Eight", "Big Turk", "Crunch", "Turtles", "Häagen-Dazs",
          "Carnation Hot Chocolate", "Milo", "Nesquik"
        ];
        
        // Extract product name from the conversation
        let productName = null;
        
        // Look for product mentions in previous messages
        for (let i = messages.length - 1; i >= 0; i--) {
          const msg = messages[i];
          if (msg.text && typeof msg.text === 'string') {
            const msg_lower = msg.text.toLowerCase();
            
            // Try direct matching of product names
            for (const name of productNames) {
              // Try exact match
              if (msg.text.includes(name) || msg_lower.includes(name.toLowerCase())) {
                productName = name;
                break;
              }
              
              // Try normalized matching (remove spaces and special characters)
              const normalized_name = name.toLowerCase().replace(/[^a-z0-9]/g, '');
              const normalized_msg = msg_lower.replace(/[^a-z0-9]/g, '');
              
              if (normalized_msg.includes(normalized_name)) {
                productName = name;
                break;
              }
            }
            
            if (productName) break;
          }
        }
        
        try {
          // Find nearby stores based on location and product
          const storeResponse = await ApiService.findNearbyStores(location, productName);
          const nearbyStores = storeResponse.data.stores;
          
          // Update the original message with the results
          const finalMessages = [...messages];
          
          if (nearbyStores && nearbyStores.length > 0) {
            // Update the original message with stores data
            finalMessages[messageIndexToUpdate] = {
              ...messageToUpdate,
              text: messageToUpdate.text,
              isLoading: false,
              stores: nearbyStores,
              hasPurchaseIntent: true
            };
          } else {
            // No stores found
            finalMessages[messageIndexToUpdate] = {
              ...messageToUpdate,
              text: messageToUpdate.text + "\n\nI couldn't find any nearby stores that carry " + 
                   (productName ? productName : "Nestle products") + 
                   " within a reasonable distance. You can still purchase online through retailers like Amazon.",
              isLoading: false,
              hasPurchaseIntent: true
            };
          }
          
          setMessages(finalMessages);
        } catch (error) {
          console.error("Error fetching nearby stores:", error);
          
          // Update message with error
          const errorMessages = [...messages];
          errorMessages[messageIndexToUpdate] = {
            ...messageToUpdate,
            text: messageToUpdate.text + "\n\nI had trouble finding nearby stores. Please try again later.",
            isLoading: false,
            hasPurchaseIntent: true
          };
          
          setMessages(errorMessages);
        }
        
        setIsGettingLocation(false);
      },
      // Error callback
      (error) => {
        console.error("Error getting location:", error);
        setIsGettingLocation(false);
        
        // Add error message based on the error code
        let errorMessage = "I couldn't access your location. ";
        
        switch(error.code) {
          case error.PERMISSION_DENIED:
            errorMessage += "You denied permission to access your location.";
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage += "Location information is unavailable.";
            break;
          case error.TIMEOUT:
            errorMessage += "The request to get your location timed out.";
            break;
          default:
            errorMessage += "An unknown error occurred.";
        }
        
        // Update the original message with the error
        const errorMessages = [...messages];
        errorMessages[messageIndexToUpdate] = {
          ...messageToUpdate,
          text: messageToUpdate.text + "\n\n" + errorMessage,
          isLoading: false,
          hasPurchaseIntent: true
        };
        
        setMessages(errorMessages);
      },
      // Options
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };
  
  /**
   * Check if a message contains purchase intent
   */
  const checkPurchaseIntent = (message) => {
    const messageLower = message.toLowerCase();
    
    // Exact patterns for purchase intent
    const strongBuyIntentPatterns = [
      /where (can|could) (i|we) (buy|purchase|get|find)/i,
      /how (can|could) (i|we) (buy|purchase|get|find)/i,
      /where (to|do you) (buy|purchase|get|find)/i,
      /(buy|purchase) online/i,
      /shopping for/i,
      /order online/i,
      /nearby stores?/i,
      /stores? near/i,
      /where.*(sell|sold)/i
    ];
    
    // Check for strong purchase intent
    for (const pattern of strongBuyIntentPatterns) {
      if (pattern.test(messageLower)) {
        return true;
      }
    }
    
    // If message contains purchase-related words and product names, it might also be purchase intent
    const buyKeywords = /(buy|purchase|shop|order)/i;
    const productKeywords = /(kitkat|kit kat|nescafe|smarties|perrier|chocolate|coffee|water|nestle)/i;
    
    if (buyKeywords.test(messageLower) && productKeywords.test(messageLower)) {
      return true;
    }
    
    // Special case: "where can I find X" is likely purchase intent
    if (/where can (i|we) find/i.test(messageLower) && productKeywords.test(messageLower)) {
      return true;
    }
    
    // Default is not purchase intent
    return false;
  };
  
  /**
   * Handles sending user message and getting response from API
   */
  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    // Check if the message contains purchase intent keywords
    const hasPurchaseIntent = checkPurchaseIntent(input);
    
    // Add user message
    const userMessage = {
      id: messages.length + 1,
      text: input,
      isBot: false,
      hasPurchaseIntent: hasPurchaseIntent
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
      isLoading: true,
      hasPurchaseIntent: hasPurchaseIntent
    };
    
    setMessages(prev => [...prev, loadingMessage]);
    scrollToBottom();
    
    let retryCount = 0;
    
    while (retryCount <= MAX_RETRY_ATTEMPTS) {
      try {
        // Use API service to send message, always including location if available
        // This ensures that when asking about products after sharing location,
        // the API will return both online and offline purchase options
        const response = await ApiService.sendChatMessage(input, sessionId, userLocation);
        
        // Store session ID
        if (response.data.session_id) {
          setSessionId(response.data.session_id);
        }
        
        // Remove loading message
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
        
        // If there's no store data but we have location and it's a purchase query,
        // fetch nearby stores directly
        if (hasPurchaseIntent && userLocation && !response.data.stores) {
          try {
            // Try to extract product name from the response or query
            let productName = null;
            
            // Define standard product names for potential matches
            const productNames = [
              "KitKat", "Nescafé", "Smarties", "Nestea", "Perrier", 
              "San Pellegrino", "Coffee Crisp", "Aero", "Nestlé Pure Life", "MAGGI",
              "After Eight", "Big Turk", "Crunch", "Turtles", "Häagen-Dazs",
              "Carnation Hot Chocolate", "Milo", "Nesquik"
            ];
            
            try {
              // First try direct pattern matching for product names
              const input_lower = input.toLowerCase();
              
              // Try direct matching of product names
              for (const name of productNames) {
                // Try exact match
                if (input.includes(name) || input_lower.includes(name.toLowerCase())) {
                  productName = name;
                  break;
                }
                
                // Try normalized matching (remove spaces and special characters)
                const normalized_name = name.toLowerCase().replace(/[^a-z0-9]/g, '');
                const normalized_input = input_lower.replace(/[^a-z0-9]/g, '');
                
                if (normalized_input.includes(normalized_name) || normalized_name.includes(normalized_input)) {
                  productName = name;
                  break;
                }
              }
              
              // If still no match found, try looking in the response
              if (!productName && response.data.response) {
                const response_lower = response.data.response.toLowerCase();
                
                for (const name of productNames) {
                  if (response.data.response.includes(name) || response_lower.includes(name.toLowerCase())) {
                    productName = name;
                    break;
                  }
                }
              }
            } catch (error) {
              console.error("Error in product name extraction:", error);
            }
            
            if (productName) {
              // Fetch nearby stores for this product
              const storeResponse = await ApiService.findNearbyStores(userLocation, productName);
              if (storeResponse.data.stores && storeResponse.data.stores.length > 0) {
                // Add stores to the response data
                response.data.stores = storeResponse.data.stores;
              }
            }
          } catch (storeError) {
            console.error("Error fetching additional store data:", storeError);
          }
        }
        
        // Add bot response
        const botMessage = {
          id: loadingMessageId,
          text: response.data.response,
          isBot: true,
          references: response.data.references || [],
          stores: response.data.stores || null,
          purchase_link: response.data.purchase_link || null,
          product_info: response.data.product_info || null,
          hasPurchaseIntent: hasPurchaseIntent
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
                  <>
                    <ReactMarkdown>
                      {message.text}
                    </ReactMarkdown>
                    
                    {/* Display purchase information if available */}
                    {message.isBot && message.hasPurchaseIntent && (message.product_info || message.purchase_link) && (
                      <ProductInfo>
                        {message.product_info && (
                          <>
                            <ProductTitle>{message.product_info.name}</ProductTitle>
                            <div>{message.product_info.description}</div>
                          </>
                        )}
                        
                        {message.purchase_link && (
                          <PurchaseLink 
                            href={message.purchase_link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                          >
                            <img src="https://embeddedcloud.pricespider.com/seller_md/141172.png" alt="Amazon" />
                            Shop on Amazon
                          </PurchaseLink>
                        )}
                      </ProductInfo>
                    )}
                    
                    {/* Display nearby stores if available */}
                    {message.isBot && message.hasPurchaseIntent && message.stores && message.stores.length > 0 && (
                      <StoresContainer>
                        <ProductTitle>Nearby Stores:</ProductTitle>
                        {message.stores.map((store, idx) => (
                          <StoreItem key={idx}>
                            <StoreHeader>
                              <StoreName>{store.name}</StoreName>
                              <StoreDistance>{store.distance} km</StoreDistance>
                            </StoreHeader>
                            <StoreAddress>{store.address}</StoreAddress>
                          </StoreItem>
                        ))}
                      </StoresContainer>
                    )}
                    
                    {/* Show location request button if purchase query but no location */}
                    {message.isBot && 
                     !userLocation && 
                     !message.stores && 
                     message.hasPurchaseIntent &&
                     index === messages.length - 1 && (
                      <LocationButton 
                        onClick={getUserLocation}
                        disabled={isGettingLocation}
                      >
                        {isGettingLocation ? 'Getting location...' : 'Share my location to find nearby stores'}
                      </LocationButton>
                    )}
                  </>
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