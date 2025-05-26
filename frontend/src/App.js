import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import styled from 'styled-components';
import ChatBot from './components/ChatBot';
import GraphManager from './components/GraphManager';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
`;

const Header = styled.header`
  background-color: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 10;
`;

const SiteName = styled.h1`
  margin: 0;
  font-size: 22px;
  color: #007a33;
`;

const Navigation = styled.nav`
  display: flex;
  gap: 20px;
`;

const NavLink = styled(Link)`
  color: #004d91;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;

  &:hover {
    color: #007a33;
    text-decoration: underline;
  }
`;

const MainContent = styled.main`
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0;
  background-image: url('/images/nestlewebsite.png');
  background-size: cover;
  background-position: center top;
  position: relative;
`;

const ChatBotContainer = styled.div`
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  max-height: 80vh;
  max-width: 90vw;
  display: flex;
  justify-content: flex-end;
  align-items: flex-end;
`;

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };

  return (
    <Router>
    <AppContainer>
      <Header>
        <SiteName>Nestle</SiteName>
          <Navigation>
            <NavLink to="/">Home</NavLink>
            <NavLink to="/graph-manager">Knowledge Graph Manager</NavLink>
          </Navigation>
      </Header>
        
        <Routes>
          <Route path="/graph-manager" element={<GraphManager />} />
          <Route path="/" element={
      <MainContent>
        <ChatBotContainer>
          <ChatBot isOpen={isChatOpen} toggleChat={toggleChat} />
        </ChatBotContainer>
      </MainContent>
          } />
        </Routes>
    </AppContainer>
    </Router>
  );
}

export default App; 