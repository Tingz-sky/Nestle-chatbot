import axios from 'axios';

// Environment configuration - auto-detects production or development
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://nestlechatbot-api-fhbxhbfcb9d9hkfn.canadacentral-01.azurewebsites.net'
  : '';  // Empty string will use the proxy in development

/**
 * Service for handling API calls to the backend
 */
class ApiService {
  /**
   * Send a chat message to the API
   * @param {string} message - User's message
   * @param {string|null} sessionId - Session ID for conversation continuity
   * @param {number} timeout - Request timeout in milliseconds
   * @returns {Promise} - Promise with the API response
   */
  static async sendChatMessage(message, sessionId = null, timeout = 20000) {
    const endpoint = `${API_BASE_URL}/api/chat`;
    
    return axios.post(endpoint, {
      query: message,
      session_id: sessionId
    }, {
      timeout: timeout
    });
  }
  
  /**
   * Trigger content refresh on the backend
   * @returns {Promise} - Promise with the API response
   */
  static async refreshContent() {
    const endpoint = `${API_BASE_URL}/api/refresh-content`;
    return axios.post(endpoint);
  }
  
  /**
   * Check the status of backend services
   * @returns {Promise} - Promise with the API response
   */
  static async checkStatus() {
    const endpoint = `${API_BASE_URL}/api/status`;
    return axios.get(endpoint);
  }

  /**
   * Get all nodes from the knowledge graph
   * @returns {Promise} - Promise with the API response
   */
  static async getNodes() {
    const endpoint = `${API_BASE_URL}/api/graph/nodes`;
    return axios.get(endpoint);
  }

  /**
   * Get all relationships from the knowledge graph
   * @returns {Promise} - Promise with the API response
   */
  static async getRelationships() {
    const endpoint = `${API_BASE_URL}/api/graph/relationships`;
    return axios.get(endpoint);
  }

  /**
   * Add a new node to the knowledge graph
   * @param {Object} nodeData - Node data with title, content, url, and type
   * @returns {Promise} - Promise with the API response
   */
  static async addNode(nodeData) {
    const endpoint = `${API_BASE_URL}/api/graph/node`;
    return axios.post(endpoint, nodeData);
  }

  /**
   * Delete a node from the knowledge graph
   * @param {string} url - URL of the node to delete
   * @returns {Promise} - Promise with the API response
   */
  static async deleteNode(url) {
    const endpoint = `${API_BASE_URL}/api/graph/node`;
    return axios.delete(endpoint, { data: { url } });
  }

  /**
   * Add a new relationship between nodes in the knowledge graph
   * @param {Object} relationshipData - Relationship data with source_url, target_url, rel_type, and properties
   * @returns {Promise} - Promise with the API response
   */
  static async addRelationship(relationshipData) {
    const endpoint = `${API_BASE_URL}/api/graph/relationship`;
    return axios.post(endpoint, relationshipData);
  }

  /**
   * Delete a relationship between nodes in the knowledge graph
   * @param {Object} relationshipData - Relationship data with source_url, target_url, and rel_type
   * @returns {Promise} - Promise with the API response
   */
  static async deleteRelationship(relationshipData) {
    const endpoint = `${API_BASE_URL}/api/graph/relationship`;
    return axios.delete(endpoint, { data: relationshipData });
  }

  /**
   * Run a custom Cypher query on the knowledge graph
   * @param {string} cypherQuery - Cypher query to execute
   * @returns {Promise} - Promise with the API response
   */
  static async runCustomQuery(cypherQuery) {
    const endpoint = `${API_BASE_URL}/api/graph/query`;
    return axios.post(endpoint, { cypher_query: cypherQuery });
  }
}

export default ApiService; 