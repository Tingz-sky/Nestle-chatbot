import os
import logging
import json
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    def __init__(self, api_key: str, endpoint: str, deployment_name: str, api_version: str = "2023-05-15"):
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        
        # Initialize OpenAI client if credentials are provided
        if api_key and endpoint and deployment_name:
            try:
                # Configure the Azure OpenAI client
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
                
                logger.info(f"Initialized Azure OpenAI service using deployment {deployment_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI service: {str(e)}")
        else:
            logger.warning("Azure OpenAI credentials not provided")
    
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def generate_response(self, 
                         query: str, 
                         context: List[Dict[str, Any]],
                         temperature: float = 0.7,
                         max_tokens: int = 500) -> str:
        """
        Generate a response to the user's query using Azure OpenAI and the provided context
        """
        try:
            # 设置令牌限制，为回复留出空间
            token_limit = 15000  # 为回复和其他系统消息留出约1000个令牌的空间
            
            # 构造系统消息
            system_message = """You are a helpful, friendly assistant for Nestle products and information.

GUIDELINES FOR RESPONSES:
1. Use the provided context to answer the user's question.
2. If the answer is not contained within the context, NEVER use phrases like "From the context provided, there isn't a specific X mentioned." Instead:
   - Suggest related products or information you do know about
   - Offer to help with other Nestle-related questions
   - Recommend checking the Nestle website for the most up-to-date information
3. Make your response conversational, helpful and friendly.
4. Include specific product details when available.
5. Format your responses nicely using simple text:
   - Do not use bold formatting for product names or any other text
   - Use plain text for all content
   - Use bullet points for lists when appropriate
   - Keep formatting minimal and clean
6. Your tone should be warm, helpful and enthusiastic about Nestle products.
7. Avoid any repetitive, formulaic language patterns.
8. Never mention "context" in your responses.
9. Always maintain the natural flow of conversation."""
            
            # 估算token数量（粗略估计：每4个字符约1个token）
            system_tokens = len(system_message) // 4
            query_tokens = len(query) // 4
            available_context_tokens = token_limit - system_tokens - query_tokens - 100  # 额外缓冲
            
            # 格式化上下文，但限制其长度
            formatted_context = self._format_context_with_limit(context, available_context_tokens)
            
            # 构造用户消息
            user_message = f"Context:\n{formatted_context}\n\nQuestion: {query}"
            
            # 调用Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                n=1
            )
            
            # 提取生成的文本
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return "I'm sorry, I couldn't generate a response."
                
        except Exception as e:
            logger.error(f"Error generating response from Azure OpenAI: {str(e)}")
            return f"I apologize, but I'm having trouble processing your request. Please try again later."
    
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def generate_response_with_history(self,
                                     query: str,
                                     context: List[Dict[str, Any]],
                                     chat_history: List[Dict[str, Any]],
                                     temperature: float = 0.7,
                                     max_tokens: int = 500) -> str:
        """
        Generate a response to the user's query using Azure OpenAI with conversation history
        
        Args:
            query: The user's current question
            context: The retrieved information from knowledge sources
            chat_history: List of previous messages, each with 'type' and 'content' keys
            temperature: Sampling temperature for the model
            max_tokens: Maximum tokens for the response
            
        Returns:
            The generated response text
        """
        try:
            # Set token limit budget
            token_limit = 14000  # Reserve about 2000 tokens for response and system message
            
            # Construct system message
            system_message = """You are a helpful, friendly assistant for Nestle products and information.

GUIDELINES FOR RESPONSES:
1. Use the provided context to answer the user's question.
2. Remember the conversation history to provide contextually relevant responses.
3. If the answer is not contained within the context, NEVER use phrases like "From the context provided, there isn't a specific X mentioned." Instead:
   - Suggest related products or information you do know about
   - Offer to help with other Nestle-related questions
   - Recommend checking the Nestle website for the most up-to-date information
4. Make your response conversational, helpful and friendly.
5. Include specific product details when available.
6. Format your responses nicely using simple text.
7. Your tone should be warm, helpful and enthusiastic about Nestle products.
8. Avoid any repetitive, formulaic language patterns.
9. Never mention "context" or "conversation history" in your responses.
10. Always maintain the natural flow of conversation."""
            
            # Estimate token counts
            system_tokens = len(system_message) // 4
            query_tokens = len(query) // 4
            
            # Calculate history tokens (approximate)
            history_tokens = 0
            for message in chat_history:
                history_tokens += len(message["content"]) // 4 + 10  # Add overhead for message metadata
            
            # Calculate available tokens for context
            available_context_tokens = token_limit - system_tokens - query_tokens - history_tokens - 200  # Extra buffer
            
            # Format context within token limit
            formatted_context = self._format_context_with_limit(context, available_context_tokens)
            
            # Prepare messages array for API call
            messages = [{"role": "system", "content": system_message}]
            
            # Add conversation history
            for message in chat_history:
                if message["type"] == "human":
                    messages.append({"role": "user", "content": message["content"]})
                elif message["type"] == "ai":
                    messages.append({"role": "assistant", "content": message["content"]})
            
            # Add current context and query
            current_query = f"Context:\n{formatted_context}\n\nQuestion: {query}"
            messages.append({"role": "user", "content": current_query})
            
            # Call Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1
            )
            
            # Extract generated text
            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                return "I'm sorry, I couldn't generate a response."
                
        except Exception as e:
            logger.error(f"Error generating response with history: {str(e)}")
            return f"I apologize, but I'm having trouble processing your request. Please try again later."
    
    def generate_cypher_query(self, user_query: str) -> str:
        """
        Generate a Cypher query based on the user's natural language query
        """
        try:
            # System message with instructions for generating Cypher
            system_message = """You are a helpful assistant that converts natural language questions about Nestle products into Cypher queries for Neo4j.
            The graph database has the following structure:
            - Nodes with label 'Content' represent web pages with properties: title, content, url, type
            - Nodes with label 'Entity' represent products, ingredients, etc. with properties: title, type
            - Relationships like 'MENTIONS' connect Content nodes to Entity nodes
            
            Generate a valid Cypher query that would answer the user's question.
            Your response should contain ONLY the Cypher query, nothing else. 
            DO NOT include markdown code block formatting (like ```cypher or ```) in your response."""
            
            # Call the Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Convert this question to a Cypher query: {user_query}"}
                ],
                temperature=0.1,  # Low temperature for more deterministic output
                max_tokens=300,
                n=1
            )
            
            # Extract the generated query and clean it
            if response and response.choices:
                query_text = response.choices[0].message.content.strip()
                
                # 清理可能存在的代码块标记
                query_text = query_text.replace("```cypher", "").replace("```", "").strip()
                
                return query_text
            else:
                # Fallback to a simple query if generation fails
                return """
                MATCH (n:Content)
                WHERE toLower(n.title) CONTAINS toLower($query) OR toLower(n.content) CONTAINS toLower($query)
                RETURN n.title as title, n.content as content, n.url as url
                LIMIT 5
                """
                
        except Exception as e:
            logger.error(f"Error generating Cypher query: {str(e)}")
            # Return a simple fallback query
            return """
            MATCH (n:Content) 
            WHERE toLower(n.content) CONTAINS toLower($query)
            RETURN n.title as title, n.content as content, n.url as url
            LIMIT 5
            """
    
    def _format_context_with_limit(self, context: List[Dict[str, Any]], token_limit: int) -> str:
        """Format the context for inclusion in the prompt with a token limit"""
        formatted_text = ""
        estimated_tokens = 0
        
        for i, item in enumerate(context):
            title = item.get("title", f"Document {i+1}")
            content = item.get("content", "")
            
            # 估算当前项的token数量
            item_text = f"--- {title} ---\n{content}\n\n"
            item_tokens = len(item_text) // 4  # 粗略估计
            
            # 如果添加当前项会超出限制，则尝试截断内容
            if estimated_tokens + item_tokens > token_limit:
                remaining_tokens = token_limit - estimated_tokens
                if remaining_tokens > 30:  # 确保至少有足够的token来添加有意义的内容
                    # 截断内容以适应剩余空间
                    max_chars = remaining_tokens * 4
                    truncated_content = content[:max_chars - 20] + "..."
                    truncated_text = f"--- {title} ---\n{truncated_content}\n\n"
                    formatted_text += truncated_text
                break
            
            # 添加完整项
            formatted_text += item_text
            estimated_tokens += item_tokens
            
            # 如果已经达到限制，停止添加
            if estimated_tokens >= token_limit:
                break
        
        return formatted_text
    
    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format the context for inclusion in the prompt (no limit)"""
        formatted_text = ""
        
        for i, item in enumerate(context):
            title = item.get("title", f"Document {i+1}")
            content = item.get("content", "")
            formatted_text += f"--- {title} ---\n{content}\n\n"
            
        return formatted_text 