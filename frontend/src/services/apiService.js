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
   * @param {Object} location - Optional user location {latitude, longitude}
   * @returns {Promise} - API response
   */
  sendChatMessage: async (message, sessionId = null, location = null, timeout = 20000) => {
    try {
      const payload = { 
        query: message,
        session_id: sessionId
      };
      
      // Add location data if available
      if (location && location.latitude && location.longitude) {
        payload.latitude = location.latitude;
        payload.longitude = location.longitude;
      }
      
      console.log("Sending chat request with payload:", JSON.stringify(payload));
      
      const response = await axios.post(`${API_BASE_URL}/api/chat`, payload, {
        timeout: timeout
      });
      
      // Log response details to help with debugging
      console.log(`Chat response received. Contains stores: ${!!response.data.stores}, contains product info: ${!!response.data.product_info}, contains purchase link: ${!!response.data.purchase_link}`);
      
      return response;
    } catch (error) {
      console.error('Error sending message:', error);
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('API error response:', error.response.status, error.response.data);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('No response received from API');
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error setting up API request:', error.message);
      }
      throw error;
    }
  },
  
  /**
   * Find nearby stores based on location
   * @param {Object} location - User location {latitude, longitude}
   * @param {string} product - Optional product name to filter stores
   * @param {number} limit - Maximum number of results to return
   * @returns {Promise} - API response with nearby stores
   */
  findNearbyStores: async (location, product = null, limit = 3) => {
    try {
      const payload = {
        latitude: location.latitude,
        longitude: location.longitude,
        limit: limit
      };
      
      if (product) {
        payload.product = product;
      }
      
      return await axios.post(`${API_BASE_URL}/api/stores/nearby`, payload);
    } catch (error) {
      console.error('Error finding nearby stores:', error);
      throw error;
    }
  },
  
  /**
   * Get all available products
   * @returns {Promise} - API response with product data
   */
  getAllProducts: async () => {
    try {
      return await axios.get(`${API_BASE_URL}/api/products`);
    } catch (error) {
      console.error('Error fetching products:', error);
      throw error;
    }
  },
  
  /**
   * Get information for a specific product
   * @param {string} productName - Name of the product
   * @returns {Promise} - API response with product details
   */
  getProduct: async (productName) => {
    try {
      return await axios.get(`${API_BASE_URL}/api/products/${encodeURIComponent(productName)}`);
    } catch (error) {
      console.error(`Error fetching product '${productName}':`, error);
      throw error;
    }
  },
  
  /**
   * Get stores that sell a specific product
   * @param {string} productName - Name of the product
   * @param {Object} location - Optional user location {latitude, longitude}
   * @returns {Promise} - API response with store data
   */
  getProductStores: async (productName, location = null) => {
    try {
      let url = `${API_BASE_URL}/api/products/${encodeURIComponent(productName)}/stores`;
      
      // Add location parameters if available
      if (location && location.latitude && location.longitude) {
        url += `?latitude=${location.latitude}&longitude=${location.longitude}`;
      }
      
      return await axios.get(url);
    } catch (error) {
      console.error(`Error fetching stores for product '${productName}':`, error);
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