import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import ApiService from '../services/apiService';

// Styled components for the Graph Manager UI
const Container = styled.div`
  max-width: 100%;
  margin: 20px auto;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h2`
  color: #004d91;
  margin-bottom: 20px;
`;

const TabContainer = styled.div`
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #dee2e6;
`;

const Tab = styled.button`
  padding: 10px 20px;
  background-color: ${props => props.active ? '#004d91' : '#ffffff'};
  color: ${props => props.active ? '#ffffff' : '#004d91'};
  border: 1px solid #dee2e6;
  border-bottom: none;
  border-radius: 5px 5px 0 0;
  margin-right: 5px;
  cursor: pointer;
  font-weight: ${props => props.active ? 'bold' : 'normal'};
  transition: all 0.3s ease;

  &:hover {
    background-color: ${props => props.active ? '#004d91' : '#e9ecef'};
  }
`;

const ContentPanel = styled.div`
  background-color: #ffffff;
  border: 1px solid #dee2e6;
  border-top: none;
  border-radius: 0 0 5px 5px;
  padding: 20px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-width: 800px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
`;

const Label = styled.label`
  margin-bottom: 5px;
  font-weight: bold;
`;

const Input = styled.input`
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
`;

const TextArea = styled.textarea`
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  min-height: 100px;
`;

const Select = styled.select`
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
`;

const Button = styled.button`
  padding: 10px 20px;
  background-color: #004d91;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #003366;
  }

  &:disabled {
    background-color: #b3c1d1;
    cursor: not-allowed;
  }
`;

const TableContainer = styled.div`
  overflow-x: auto;
  margin-bottom: 20px;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #dee2e6;
`;

const Th = styled.th`
  background-color: #e9ecef;
  padding: 12px;
  text-align: left;
  border: 1px solid #dee2e6;
`;

const Td = styled.td`
  padding: 12px;
  border: 1px solid #dee2e6;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const ActionButton = styled.button`
  padding: 5px 10px;
  margin: 0 2px;
  background-color: ${props => props.danger ? '#dc3545' : '#004d91'};
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: ${props => props.danger ? '#bd2130' : '#003366'};
  }

  &:disabled {
    background-color: #b3c1d1;
    cursor: not-allowed;
  }
`;

const Alert = styled.div`
  padding: 10px 15px;
  margin: 10px 0;
  border-radius: 4px;
  background-color: ${props => props.type === 'error' ? '#f8d7da' : '#d4edda'};
  color: ${props => props.type === 'error' ? '#721c24' : '#155724'};
  border: 1px solid ${props => props.type === 'error' ? '#f5c6cb' : '#c3e6cb'};
`;

const QueryContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const QueryInput = styled.textarea`
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  min-height: 100px;
  font-family: monospace;
`;

const ResultContainer = styled.div`
  margin-top: 20px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 15px;
  background-color: #f8f9fa;
  max-height: 300px;
  overflow-y: auto;
  font-family: monospace;
  white-space: pre-wrap;
`;

// New styled component for modal
const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 80%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
  
  &:hover {
    color: #000;
  }
`;

const GraphManager = () => {
  // State for tab management
  const [activeTab, setActiveTab] = useState('nodes');
  
  // State for nodes
  const [nodes, setNodes] = useState([]);
  const [nodeForm, setNodeForm] = useState({
    title: '',
    content: '',
    url: '',
    type: 'Entity'
  });
  
  // State for node editing
  const [editingNode, setEditingNode] = useState(null);
  const [isEditingNode, setIsEditingNode] = useState(false);
  
  // State for relationships
  const [relationships, setRelationships] = useState([]);
  const [relationshipForm, setRelationshipForm] = useState({
    source_url: '',
    target_url: '',
    rel_type: 'MENTIONS',
    properties: {}
  });
  
  // State for relationship editing
  const [editingRelationship, setEditingRelationship] = useState(null);
  const [isEditingRelationship, setIsEditingRelationship] = useState(false);
  
  // State for custom query
  const [customQuery, setCustomQuery] = useState("MATCH (n) RETURN n LIMIT 10");
  const [queryResult, setQueryResult] = useState(null);
  
  // State for alerts and loading
  const [alert, setAlert] = useState({ message: '', type: '' });
  const [isLoading, setIsLoading] = useState(false);
  
  // Load initial data
  useEffect(() => {
    fetchNodes();
    fetchRelationships();
  }, []);
  
  // Fetch nodes from API
  const fetchNodes = async () => {
    try {
      setIsLoading(true);
      const response = await ApiService.getNodes();
      setNodes(response.data);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching nodes:', error);
      setAlert({
        message: 'Failed to fetch nodes: ' + (error.response?.data?.detail || error.message),
        type: 'error'
      });
      setIsLoading(false);
    }
  };
  
  // Fetch relationships from API
  const fetchRelationships = async () => {
    try {
      setIsLoading(true);
      const response = await ApiService.getRelationships();
      setRelationships(response.data);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching relationships:', error);
      setAlert({
        message: 'Failed to fetch relationships: ' + (error.response?.data?.detail || error.message),
        type: 'error'
      });
      setIsLoading(false);
    }
  };
  
  // Handle node form input changes
  const handleNodeInputChange = (e) => {
    const { name, value } = e.target;
    setNodeForm(prev => ({ ...prev, [name]: value }));
  };
  
  // Determine if content and URL are required based on node type
  const isContentRequired = nodeForm.type === 'Page';
  const isUrlRequired = nodeForm.type === 'Page';
  
  // Open edit node modal
  const handleEditNode = (node) => {
    setEditingNode(node);
    setNodeForm({
      title: node.title,
      content: node.content || '',
      url: node.url,
      type: node.label || node.type || 'Entity'
    });
    setIsEditingNode(true);
  };
  
  // Close edit node modal
  const handleCloseEditNodeModal = () => {
    setIsEditingNode(false);
    setEditingNode(null);
    setNodeForm({
      title: '',
      content: '',
      url: '',
      type: 'Entity'
    });
  };
  
  // Update node
  const handleUpdateNode = async (e) => {
    e.preventDefault();
    
    // Validate form - title is always required
    if (!nodeForm.title) {
      setAlert({ message: 'Title is required', type: 'error' });
      return;
    }
    
    // For Page type, content and URL are required
    if (nodeForm.type === 'Page' && (!nodeForm.content || !nodeForm.url)) {
      setAlert({ message: 'Content and URL are required for Page type nodes', type: 'error' });
      return;
    }
    
    try {
      setIsLoading(true);
      
      // First delete the existing node
      await ApiService.deleteNode(nodeForm.url);
      
      // Then create a new node with the updated data
      await ApiService.addNode(nodeForm);
      
      setAlert({ message: 'Node updated successfully', type: 'success' });
      
      // Close edit modal
      handleCloseEditNodeModal();
      
      // Refresh nodes list
      fetchNodes();
      fetchRelationships(); // Refresh relationships too as they might be affected
      setIsLoading(false);
    } catch (error) {
      console.error('Error updating node:', error);
      setAlert({
        message: 'Failed to update node: ' + (error.response?.data?.detail || error.message),
        type: 'error'
      });
      setIsLoading(false);
    }
  };
  
  // Submit node form
  const handleNodeSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form - title is always required
    if (!nodeForm.title) {
      setAlert({ message: 'Title is required', type: 'error' });
      return;
    }
    
    // For Page type, content and URL are required
    if (nodeForm.type === 'Page' && (!nodeForm.content || !nodeForm.url)) {
      setAlert({ message: 'Content and URL are required for Page type nodes', type: 'error' });
      return;
    }
    
    // For Entity type, generate a standard URL if not provided
    const formData = { ...nodeForm };
    if (nodeForm.type === 'Entity' && !nodeForm.url) {
      formData.url = `entity:${nodeForm.title.replace(/\s+/g, '')}`;
    }
    
    try {
      setIsLoading(true);
      await ApiService.addNode(formData);
      setAlert({ message: 'Node added successfully', type: 'success' });
      setNodeForm({
        title: '',
        content: '',
        url: '',
        type: 'Entity'
      });
      
      // Refresh nodes list
      fetchNodes();
      setIsLoading(false);
    } catch (error) {
      console.error('Error adding node:', error);
      setAlert({
        message: 'Failed to add node: ' + (error.response?.data?.detail || error.message),
        type: 'error'
      });
      setIsLoading(false);
    }
  };
  
  // Delete node
  const handleDeleteNode = async (url) => {
    if (window.confirm('Are you sure you want to delete this node? This will also delete all relationships connected to this node.')) {
      try {
        setIsLoading(true);
        await ApiService.deleteNode(url);
        
        setAlert({ message: 'Node deleted successfully', type: 'success' });
        
        // Refresh nodes and relationships lists as relationships might have been affected
        fetchNodes();
        fetchRelationships();
        setIsLoading(false);
      } catch (error) {
        console.error('Error deleting node:', error);
        setAlert({
          message: 'Failed to delete node: ' + (error.response?.data?.detail || error.message),
          type: 'error'
        });
        setIsLoading(false);
      }
    }
  };
  
  // Handle relationship form input changes
  const handleRelationshipInputChange = (e) => {
    const { name, value } = e.target;
    setRelationshipForm(prev => ({ ...prev, [name]: value }));
  };
  
  // Open edit relationship modal
  const handleEditRelationship = (relationship) => {
    setEditingRelationship(relationship);
    setRelationshipForm({
      source_url: relationship.source_url,
      target_url: relationship.target_url,
      rel_type: relationship.rel_type,
      properties: relationship.properties || {}
    });
    setIsEditingRelationship(true);
  };
  
  // Close edit relationship modal
  const handleCloseEditRelationshipModal = () => {
    setIsEditingRelationship(false);
    setEditingRelationship(null);
    setRelationshipForm({
      source_url: '',
      target_url: '',
      rel_type: 'MENTIONS',
      properties: {}
    });
  };
  
  // Update relationship
  const handleUpdateRelationship = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!relationshipForm.source_url || !relationshipForm.target_url || !relationshipForm.rel_type) {
      setAlert({ message: 'Please fill in all required fields', type: 'error' });
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Original relationship data for deletion
      const originalData = {
        source_url: editingRelationship.source_url,
        target_url: editingRelationship.target_url,
        rel_type: editingRelationship.rel_type
      };
      
      // First delete the existing relationship
      await ApiService.deleteRelationship(originalData);
      
      // Then create a new relationship with the updated data
      await ApiService.addRelationship(relationshipForm);
      
      setAlert({ message: 'Relationship updated successfully', type: 'success' });
      
      // Close edit modal
      handleCloseEditRelationshipModal();
      
      // Refresh relationships list
      fetchRelationships();
      setIsLoading(false);
    } catch (error) {
      console.error('Error updating relationship:', error);
      setAlert({
        message: 'Failed to update relationship: ' + (error.response?.data?.detail || error.message),
        type: 'error'
      });
      setIsLoading(false);
    }
  };
  
  // Submit relationship form
  const handleRelationshipSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!relationshipForm.source_url || !relationshipForm.target_url || !relationshipForm.rel_type) {
      setAlert({ message: 'Please fill in all required fields', type: 'error' });
      return;
    }
    
    try {
      setIsLoading(true);
      await ApiService.addRelationship(relationshipForm);
      setAlert({ message: 'Relationship added successfully', type: 'success' });
      setRelationshipForm({
        source_url: '',
        target_url: '',
        rel_type: 'MENTIONS',
        properties: {}
      });
      
      // Refresh relationships list
      fetchRelationships();
      setIsLoading(false);
    } catch (error) {
      console.error('Error adding relationship:', error);
      setAlert({
        message: 'Failed to add relationship: ' + (error.response?.data?.detail || error.message),
        type: 'error'
      });
      setIsLoading(false);
    }
  };
  
  // Delete relationship
  const handleDeleteRelationship = async (rel) => {
    if (window.confirm('Are you sure you want to delete this relationship?')) {
      try {
        setIsLoading(true);
        await ApiService.deleteRelationship({
          source_url: rel.source_url,
          target_url: rel.target_url,
          rel_type: rel.rel_type
        });
        
        setAlert({ message: 'Relationship deleted successfully', type: 'success' });
        
        // Refresh relationships list
        fetchRelationships();
        setIsLoading(false);
      } catch (error) {
        console.error('Error deleting relationship:', error);
        setAlert({
          message: 'Failed to delete relationship: ' + (error.response?.data?.detail || error.message),
          type: 'error'
        });
        setIsLoading(false);
      }
    }
  };
  
  // Execute custom query
  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    
    if (!customQuery) {
      setAlert({ message: 'Please enter a Cypher query', type: 'error' });
      return;
    }
    
    try {
      setIsLoading(true);
      const response = await ApiService.runCustomQuery(customQuery);
      setQueryResult(response.data.results);
      setAlert({ message: 'Query executed successfully', type: 'success' });
      setIsLoading(false);
    } catch (error) {
      console.error('Error executing query:', error);
      setAlert({
        message: 'Failed to execute query: ' + (error.response?.data?.detail || error.message),
        type: 'error'
      });
      setQueryResult(null);
      setIsLoading(false);
    }
  };
  
  return (
    <Container>
      <Title>Knowledge Graph Manager</Title>
      
      <TabContainer>
        <Tab 
          active={activeTab === 'nodes'} 
          onClick={() => setActiveTab('nodes')}
        >
          Nodes
        </Tab>
        <Tab 
          active={activeTab === 'relationships'} 
          onClick={() => setActiveTab('relationships')}
        >
          Relationships
        </Tab>
        <Tab 
          active={activeTab === 'query'} 
          onClick={() => setActiveTab('query')}
        >
          Custom Query
        </Tab>
      </TabContainer>
      
      {alert.message && (
        <Alert type={alert.type}>
          {alert.message}
        </Alert>
      )}
      
      <ContentPanel>
        {activeTab === 'nodes' && (
          <>
            <Title>Add New Node</Title>
            <Form onSubmit={handleNodeSubmit}>
              <FormGroup>
                <Label htmlFor="title">Title*</Label>
                <Input 
                  id="title"
                  name="title" 
                  value={nodeForm.title} 
                  onChange={handleNodeInputChange} 
                  placeholder="Node title"
                  required 
                />
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="content">Content{isContentRequired ? '*' : ''}</Label>
                <TextArea 
                  id="content"
                  name="content" 
                  value={nodeForm.content} 
                  onChange={handleNodeInputChange} 
                  placeholder={isContentRequired ? "Required for Page nodes" : "Optional for Entity nodes"}
                  required={isContentRequired}
                />
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="url">URL{isUrlRequired ? '*' : ''}</Label>
                <Input 
                  id="url"
                  name="url" 
                  value={nodeForm.url} 
                  onChange={handleNodeInputChange} 
                  placeholder={isUrlRequired ? "https://example.com/page" : "Optional - will be auto-generated if empty"}
                  required={isUrlRequired}
                />
                {!isUrlRequired && nodeForm.url === '' && (
                  <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '5px' }}>
                    Auto-generated URL will be: entity:{nodeForm.title.replace(/\s+/g, '')}
                  </div>
                )}
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="type">Type</Label>
                <Select 
                  id="type"
                  name="type" 
                  value={nodeForm.type} 
                  onChange={handleNodeInputChange}
                >
                  <option value="Entity">Entity (Knowledge Graph Node)</option>
                  <option value="Page">Page (Website Content)</option>
                  <option value="Product">Product</option>
                  <option value="Category">Category</option>
                  <option value="Recipe">Recipe</option>
                  <option value="Ingredient">Ingredient</option>
                </Select>
              </FormGroup>
              
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Adding...' : 'Add Node'}
              </Button>
            </Form>
            
            <Title style={{ marginTop: '30px' }}>Existing Nodes</Title>
            <TableContainer>
              <Table>
                <thead>
                  <tr>
                    <Th>Title</Th>
                    <Th>Content</Th>
                    <Th>URL</Th>
                    <Th>Type</Th>
                    <Th>Actions</Th>
                  </tr>
                </thead>
                <tbody>
                  {nodes.length > 0 ? (
                    nodes.map((node, index) => (
                      <tr key={index}>
                        <Td>{node.title}</Td>
                        <Td>{node.content}</Td>
                        <Td>{node.url}</Td>
                        <Td>{node.label || node.type}</Td>
                        <Td>
                          <ActionButton 
                            onClick={() => handleEditNode(node)}
                            disabled={isLoading}
                            style={{ marginRight: '5px' }}
                          >
                            Edit
                          </ActionButton>
                          <ActionButton 
                            danger 
                            onClick={() => handleDeleteNode(node.url)}
                            disabled={isLoading}
                          >
                            Delete
                          </ActionButton>
                        </Td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <Td colSpan="5">No nodes found</Td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </TableContainer>
          </>
        )}
        
        {activeTab === 'relationships' && (
          <>
            <Title>Add New Relationship</Title>
            <Form onSubmit={handleRelationshipSubmit}>
              <FormGroup>
                <Label htmlFor="source_url">Source Node URL*</Label>
                <Select 
                  id="source_url"
                  name="source_url" 
                  value={relationshipForm.source_url} 
                  onChange={handleRelationshipInputChange}
                  required
                >
                  <option value="">Select a source node</option>
                  {nodes.map((node, index) => (
                    <option key={`source-${index}`} value={node.url}>
                      {node.title} ({node.url})
                    </option>
                  ))}
                </Select>
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="rel_type">Relationship Type*</Label>
                <Select 
                  id="rel_type"
                  name="rel_type" 
                  value={relationshipForm.rel_type} 
                  onChange={handleRelationshipInputChange}
                  required
                >
                  <option value="MENTIONS">MENTIONS</option>
                  <option value="CONTAINS">CONTAINS</option>
                  <option value="RELATED_TO">RELATED_TO</option>
                  <option value="SIMILAR_TO">SIMILAR_TO</option>
                  <option value="INGREDIENT_OF">INGREDIENT_OF</option>
                </Select>
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="target_url">Target Node URL*</Label>
                <Select 
                  id="target_url"
                  name="target_url" 
                  value={relationshipForm.target_url} 
                  onChange={handleRelationshipInputChange}
                  required
                >
                  <option value="">Select a target node</option>
                  {nodes.map((node, index) => (
                    <option key={`target-${index}`} value={node.url}>
                      {node.title} ({node.url})
                    </option>
                  ))}
                </Select>
              </FormGroup>
              
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Adding...' : 'Add Relationship'}
              </Button>
            </Form>
            
            <Title style={{ marginTop: '30px' }}>Existing Relationships</Title>
            <TableContainer>
              <Table>
                <thead>
                  <tr>
                    <Th>Source</Th>
                    <Th>Relationship</Th>
                    <Th>Target</Th>
                    <Th>Actions</Th>
                  </tr>
                </thead>
                <tbody>
                  {relationships.length > 0 ? (
                    relationships.map((rel, index) => (
                      <tr key={index}>
                        <Td>{rel.source_title || rel.source_url}</Td>
                        <Td>{rel.rel_type}</Td>
                        <Td>{rel.target_title || rel.target_url}</Td>
                        <Td>
                          <ActionButton 
                            onClick={() => handleEditRelationship(rel)}
                            disabled={isLoading}
                            style={{ marginRight: '5px' }}
                          >
                            Edit
                          </ActionButton>
                          <ActionButton 
                            danger 
                            onClick={() => handleDeleteRelationship(rel)}
                            disabled={isLoading}
                          >
                            Delete
                          </ActionButton>
                        </Td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <Td colSpan="4">No relationships found</Td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </TableContainer>
          </>
        )}
        
        {activeTab === 'query' && (
          <QueryContainer>
            <Title>Run Custom Cypher Query</Title>
            <Form onSubmit={handleQuerySubmit}>
              <FormGroup>
                <Label htmlFor="query">Cypher Query</Label>
                <QueryInput 
                  id="query"
                  value={customQuery} 
                  onChange={(e) => setCustomQuery(e.target.value)} 
                  placeholder="MATCH (n) RETURN n LIMIT 10"
                  required 
                />
              </FormGroup>
              
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Executing...' : 'Execute Query'}
              </Button>
            </Form>
            
            {queryResult && (
              <>
                <Title>Query Results</Title>
                <ResultContainer>
                  {JSON.stringify(queryResult, null, 2)}
                </ResultContainer>
              </>
            )}
          </QueryContainer>
        )}
      </ContentPanel>
      
      {/* Edit Node Modal */}
      {isEditingNode && (
        <Modal>
          <ModalContent>
            <ModalHeader>
              <h2>Edit Node</h2>
              <CloseButton onClick={handleCloseEditNodeModal}>&times;</CloseButton>
            </ModalHeader>
            
            <Form onSubmit={handleUpdateNode}>
              <FormGroup>
                <Label htmlFor="edit-title">Title*</Label>
                <Input 
                  id="edit-title"
                  name="title" 
                  value={nodeForm.title} 
                  onChange={handleNodeInputChange} 
                  placeholder="Node title"
                  required 
                />
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="edit-content">Content{isContentRequired ? '*' : ''}</Label>
                <TextArea 
                  id="edit-content"
                  name="content" 
                  value={nodeForm.content} 
                  onChange={handleNodeInputChange} 
                  placeholder={isContentRequired ? "Required for Page nodes" : "Optional for Entity nodes"}
                  required={isContentRequired}
                />
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="edit-url">URL (cannot be changed)</Label>
                <Input 
                  id="edit-url"
                  name="url" 
                  value={nodeForm.url} 
                  readOnly
                  disabled
                  style={{ backgroundColor: '#f0f0f0' }}
                />
                <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '5px' }}>
                  The URL is the unique identifier and cannot be changed
                </div>
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="edit-type">Type</Label>
                <Select 
                  id="edit-type"
                  name="type" 
                  value={nodeForm.type} 
                  onChange={handleNodeInputChange}
                >
                  <option value="Entity">Entity (Knowledge Graph Node)</option>
                  <option value="Page">Page (Website Content)</option>
                  <option value="Product">Product</option>
                  <option value="Category">Category</option>
                  <option value="Recipe">Recipe</option>
                  <option value="Ingredient">Ingredient</option>
                </Select>
              </FormGroup>
              
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Updating...' : 'Update Node'}
              </Button>
            </Form>
          </ModalContent>
        </Modal>
      )}
      
      {/* Edit Relationship Modal */}
      {isEditingRelationship && (
        <Modal>
          <ModalContent>
            <ModalHeader>
              <h2>Edit Relationship</h2>
              <CloseButton onClick={handleCloseEditRelationshipModal}>&times;</CloseButton>
            </ModalHeader>
            
            <Form onSubmit={handleUpdateRelationship}>
              <FormGroup>
                <Label htmlFor="edit-source-url">Source Node URL*</Label>
                <Select 
                  id="edit-source-url"
                  name="source_url" 
                  value={relationshipForm.source_url} 
                  onChange={handleRelationshipInputChange}
                  required
                >
                  <option value="">Select a source node</option>
                  {nodes.map((node, index) => (
                    <option key={`edit-source-${index}`} value={node.url}>
                      {node.title} ({node.url})
                    </option>
                  ))}
                </Select>
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="edit-rel-type">Relationship Type*</Label>
                <Select 
                  id="edit-rel-type"
                  name="rel_type" 
                  value={relationshipForm.rel_type} 
                  onChange={handleRelationshipInputChange}
                  required
                >
                  <option value="MENTIONS">MENTIONS</option>
                  <option value="CONTAINS">CONTAINS</option>
                  <option value="RELATED_TO">RELATED_TO</option>
                  <option value="SIMILAR_TO">SIMILAR_TO</option>
                  <option value="INGREDIENT_OF">INGREDIENT_OF</option>
                </Select>
              </FormGroup>
              
              <FormGroup>
                <Label htmlFor="edit-target-url">Target Node URL*</Label>
                <Select 
                  id="edit-target-url"
                  name="target_url" 
                  value={relationshipForm.target_url} 
                  onChange={handleRelationshipInputChange}
                  required
                >
                  <option value="">Select a target node</option>
                  {nodes.map((node, index) => (
                    <option key={`edit-target-${index}`} value={node.url}>
                      {node.title} ({node.url})
                    </option>
                  ))}
                </Select>
              </FormGroup>
              
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Updating...' : 'Update Relationship'}
              </Button>
            </Form>
          </ModalContent>
        </Modal>
      )}
    </Container>
  );
};

export default GraphManager; 