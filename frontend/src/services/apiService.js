import axios from 'axios';

// Environment configuration - auto-detects production or development
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://nestlechatbot-api-fhbxhbfcb9d9hkfn.canadacentral-01.azurewebsites.net'
  : '';  // Empty string will use the proxy in development

/**
 * Service for interacting with the backend API
 */
const ApiService = {
  /**
   * Send a chat message to the API
   * @param {string} message - The user's message
   * @param {string} sessionId - Optional session ID for continuing a conversation
   * @returns {Promise} - API response
   */
  sendChatMessage: async (message, sessionId = null, timeout = 20000) => {
    try {
      const payload = { 
        query: message,
        session_id: sessionId
      };
      
      return await axios.post(`${API_BASE_URL}/api/chat`, payload, {
        timeout: timeout
      });
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },
  
  /**
   * Clear the conversation history for a session
   * @param {string} sessionId - The session ID to clear
   * @returns {Promise} - API response
   */
  clearConversation: async (sessionId) => {
    try {
      return await axios.delete(`${API_BASE_URL}/api/conversation/${sessionId}`);
    } catch (error) {
      console.error('Error clearing conversation:', error);
      throw error;
    }
  },
  
  /**
   * Get all nodes from the knowledge graph
   * @returns {Promise} - API response with nodes data
   */
  getNodes: async () => {
    try {
      return await axios.get(`${API_BASE_URL}/api/graph/nodes`);
    } catch (error) {
      console.error('Error fetching nodes:', error);
      throw error;
    }
  },
  
  /**
   * Get all relationships from the knowledge graph
   * @returns {Promise} - API response with relationship data
   */
  getRelationships: async () => {
    try {
      return await axios.get(`${API_BASE_URL}/api/graph/relationships`);
    } catch (error) {
      console.error('Error fetching relationships:', error);
      throw error;
    }
  },
  
  /**
   * Add a new node to the knowledge graph
   * @param {Object} nodeData - Data for the new node
   * @returns {Promise} - API response
   */
  addNode: async (nodeData) => {
    try {
      return await axios.post(`${API_BASE_URL}/api/graph/node`, nodeData);
    } catch (error) {
      console.error('Error adding node:', error);
      throw error;
    }
  },
  
  /**
   * Delete a node from the knowledge graph
   * @param {string} url - URL identifier of the node to delete
   * @returns {Promise} - API response
   */
  deleteNode: async (url) => {
    try {
      return await axios.delete(`${API_BASE_URL}/api/graph/node`, { data: { url } });
    } catch (error) {
      console.error('Error deleting node:', error);
      throw error;
    }
  },
  
  /**
   * Add a new relationship to the knowledge graph
   * @param {Object} relationshipData - Data for the new relationship
   * @returns {Promise} - API response
   */
  addRelationship: async (relationshipData) => {
    try {
      return await axios.post(`${API_BASE_URL}/api/graph/relationship`, relationshipData);
    } catch (error) {
      console.error('Error adding relationship:', error);
      throw error;
    }
  },
  
  /**
   * Delete a relationship from the knowledge graph
   * @param {Object} relationshipData - Data identifying the relationship to delete
   * @returns {Promise} - API response
   */
  deleteRelationship: async (relationshipData) => {
    try {
      return await axios.delete(`${API_BASE_URL}/api/graph/relationship`, { data: relationshipData });
    } catch (error) {
      console.error('Error deleting relationship:', error);
      throw error;
    }
  },
  
  /**
   * Run a custom Cypher query
   * @param {string} cypherQuery - The Cypher query to execute
   * @returns {Promise} - API response with query results
   */
  runCustomQuery: async (cypherQuery) => {
    try {
      return await axios.post(`${API_BASE_URL}/api/graph/query`, { cypher_query: cypherQuery });
    } catch (error) {
      console.error('Error running custom query:', error);
      throw error;
    }
  },
  
  /**
   * Check API server status
   * @returns {Promise} - API response with status information
   */
  checkStatus: async () => {
    try {
      return await axios.get(`${API_BASE_URL}/api/status`);
    } catch (error) {
      console.error('Error checking API status:', error);
      throw error;
    }
  },
  
  /**
   * Trigger content refresh on the backend
   * @returns {Promise} - API response
   */
  refreshContent: async () => {
    try {
      return await axios.post(`${API_BASE_URL}/api/refresh-content`);
    } catch (error) {
      console.error('Error refreshing content:', error);
      throw error;
    }
  }
};

export default ApiService; 