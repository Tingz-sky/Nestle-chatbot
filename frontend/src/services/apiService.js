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
}

export default ApiService; 