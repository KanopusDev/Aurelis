import os
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from .ai import GPT4, CohereEmbeddings
from .internet import WebSearch, SearchResult
from .reasoner import Reasoner, ReasoningResult
from .file import FileManager

logger = logging.getLogger(__name__)

class AurelisServices:
    def __init__(self):
        """Initialize core services for the Aurelis assistant."""
        try:
            logger.info("Initializing GPT4 service")
            self.gpt4 = GPT4()
            
            logger.info("Initializing reasoning service")
            self.reasoner = Reasoner()
            
            logger.info("Initializing embeddings service")
            self.embeddings = CohereEmbeddings()
            
            self.web_search: Optional[WebSearch] = None
            self.file_manager = FileManager()
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise

    def initialize_web_search(self, google_api_key: str, google_cx: str):
        """Initialize web search with Google API credentials"""
        try:
            self.web_search = WebSearch(google_api_key, google_cx)
            logger.info("Web search services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize web search: {str(e)}")
            raise RuntimeError(f"Web search initialization failed: {str(e)}")

    def process_with_files(self, prompt: str) -> tuple[str, list[str]]:
        """Process prompt and handle file references"""
        file_refs = self.file_manager.parse_file_references(prompt)
        
        # Attach files to context
        attached_files = []
        for ref in file_refs:
            context = self.file_manager.attach_file(ref)
            if context and not context.is_temp:
                attached_files.append(ref)
        
        return prompt, attached_files

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text"""
        return self.embeddings.embed([text])[0]

    def code_assist(self, prompt: str, with_reasoning: bool = False, 
                   with_search: bool = False, context: str = "") -> tuple[str, Optional[ReasoningResult]]:
        """Process a code assistance request"""
        try:
            if context:
                prompt = f"Previous context:\n{context}\n\nCurrent query: {prompt}"
            
            # Process file references in prompt
            prompt, files = self.process_with_files(prompt)
            
            # Add file context
            if files:
                prompt = f"Files referenced: {', '.join(files)}\n{prompt}"
            
            # Get search results if enabled
            search_results = None
            if with_search and self.web_search:
                try:
                    search_results = self.web_search.combined_search(prompt)
                    if search_results:
                        prompt += f"\n\nSearch context:\n{self._format_search_results(search_results)}"
                except Exception as e:
                    logger.error(f"Search failed: {str(e)}")
            
            # Generate response with appropriate system message
            response = self.gpt4.generate(prompt)
            
            # Handle any code blocks in response
            if "```" in response.content:
                try:
                    saved_files = self._handle_code_blocks(response.content)
                    if saved_files:
                        response.content += "\n\nFiles created/updated:\n" + "\n".join(str(f) for f in saved_files)
                except Exception as e:
                    logger.error(f"Failed to save code blocks: {str(e)}")
                    response.content += f"\n\nWarning: Failed to save some code blocks: {str(e)}"
            
            # Process reasoning if enabled
            if with_reasoning:
                try:
                    reasoning = self.reasoner.analyze(response.content, prompt)
                    return response.content, reasoning
                except Exception as e:
                    logger.error(f"Reasoning failed: {str(e)}")
                    return response.content, None
            
            return response.content, None
            
        except Exception as e:
            logger.error(f"Error in code_assist: {str(e)}")
            raise

    def _format_search_results(self, results: List[SearchResult]) -> str:
        return "\n".join(
            f"[{r.source.upper()}] {r.title}\n{r.snippet}\nSource: {r.url}"
            for r in results
        )

    def _format_response_with_citations(self, content: str, reasoning: ReasoningResult, 
                                      search_results: Optional[List[SearchResult]]) -> str:
        citations = []
        
        # Add reasoning sources
        for source, type_ in reasoning.sources.items():
            citations.append(f"[{source}: {type_}]")
        
        # Add search sources
        if search_results:
            for result in search_results:
                citations.append(f"[{result.source.upper()}: {result.url}]")
        
        return f"{content}\n\nSources:\n" + "\n".join(citations)

    def analyze_file(self, file_path: str, query: str, with_reasoning: bool = False):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            file_ext = Path(file_path).suffix
            prompt = f"""
            Analyzing file with extension: {file_ext}
            Content:
            ```
            {content}
            ```
            Query: {query}
            """
            
            response = self.gpt4.generate(prompt)
            
            if with_reasoning:
                reasoning = self.reasoner.analyze(content, query)
                return response.content, reasoning
            return response.content, None
            
        except Exception as e:
            raise RuntimeError(f"Error analyzing file: {str(e)}")

    def edit_file(self, file_path: str, instructions: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            file_ext = Path(file_path).suffix
            prompt = f"""
            Edit the following file according to instructions.
            File type: {file_ext}
            Current content:
            ```
            {content}
            ```
            Instructions: {instructions}
            
            Provide only the modified content without any explanations.
            """
            
            response = self.gpt4.generate(prompt)
            return response.content
            
        except Exception as e:
            raise RuntimeError(f"Error editing file: {str(e)}")

    def search_and_assist(self, query: str):
        if not self.web_search:
            raise RuntimeError("Web search not initialized")
        
        search_results = self.web_search.combined_search(query)
        context = "\n".join(
            f"[{r.source.upper()}]\nTitle: {r.title}\n{r.snippet}\nURL: {r.url}\n"
            for r in search_results
        )
        
        prompt = f"""Based on these search results:
        {context}
        
        Please provide a comprehensive answer for: {query}"""
        
        return self.gpt4.generate(prompt).content

    def _handle_code_blocks(self, content: str):
        """Extract and save code blocks with file references"""
        import re
        
        # Find code blocks with file references - improved pattern
        pattern = r'```(?:python)?\s*#\s*([\w\-./\\]+)[\s\n]+(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        saved_files = []
        try:
            for match in matches:
                file_ref, code = match.groups()
                saved_path = self.file_manager.save_file(file_ref, code.strip())
                saved_files.append(saved_path)
                logger.info(f"Saved code block to {saved_path}")
            return saved_files
        except Exception as e:
            logger.error(f"Error handling code blocks: {str(e)}")
            raise

    def cleanup(self):
        """Cleanup resources"""
        self.file_manager.cleanup()
