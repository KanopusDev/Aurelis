"""Context management and intelligent code chunking for AI model processing."""

import ast
import hashlib
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

from aurelis.core.types import CodeChunk, ChunkingStrategy, Configuration
from aurelis.core.config import get_config
from aurelis.core.logging import get_logger
from aurelis.core.cache import get_cache_manager
from aurelis.core.exceptions import ChunkingError


@dataclass
class DependencyInfo:
    """Information about code dependencies."""
    imports: Set[str] = field(default_factory=set)
    functions: Set[str] = field(default_factory=set)
    classes: Set[str] = field(default_factory=set)
    variables: Set[str] = field(default_factory=set)
    external_calls: Set[str] = field(default_factory=set)


@dataclass
class CodeContext:
    """Rich context information for code processing."""
    chunks: List[CodeChunk]
    dependencies: DependencyInfo
    file_info: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseChunker(ABC):
    """Abstract base class for code chunking strategies."""
    
    def __init__(self, config: Configuration):
        self.config = config
        self.logger = get_logger(f"chunking.{self.__class__.__name__.lower()}")
    
    @abstractmethod
    def chunk_code(self, code: str, file_path: Path) -> List[CodeChunk]:
        """Chunk code into processable segments."""
        pass
    
    def _generate_chunk_id(self, file_path: Path, start_line: int, end_line: int) -> str:
        """Generate unique chunk ID."""
        content = f"{file_path}:{start_line}:{end_line}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimation: 1 token ≈ 4 characters for code
        return len(text) // 4
    
    def _extract_dependencies(self, code: str) -> DependencyInfo:
        """Extract dependency information from code."""
        dependencies = DependencyInfo()
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.imports.add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.imports.add(node.module)
                    if node.names:
                        for alias in node.names:
                            dependencies.imports.add(alias.name)
                
                elif isinstance(node, ast.FunctionDef):
                    dependencies.functions.add(node.name)
                
                elif isinstance(node, ast.ClassDef):
                    dependencies.classes.add(node.name)
                
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    dependencies.variables.add(node.id)
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        dependencies.external_calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            dependencies.external_calls.add(f"{node.func.value.id}.{node.func.attr}")
        
        except SyntaxError:
            # If parsing fails, continue with empty dependencies
            pass
        
        return dependencies


class SlidingWindowChunker(BaseChunker):
    """Sliding window chunker with overlapping contexts."""
    
    def chunk_code(self, code: str, file_path: Path) -> List[CodeChunk]:
        """Chunk code using sliding window approach."""
        lines = code.split('\n')
        chunks = []
        
        chunk_size_lines = self._estimate_lines_per_chunk()
        overlap_lines = int(chunk_size_lines * self.config.overlap_ratio)
        
        start_line = 0
        chunk_index = 0
        
        while start_line < len(lines):
            end_line = min(start_line + chunk_size_lines, len(lines))
            chunk_lines = lines[start_line:end_line]
            chunk_content = '\n'.join(chunk_lines)
            
            # Skip empty chunks
            if not chunk_content.strip():
                start_line = end_line
                continue
            
            chunk_id = self._generate_chunk_id(file_path, start_line + 1, end_line)
            dependencies = self._extract_dependencies(chunk_content)
            
            chunk = CodeChunk(
                id=chunk_id,
                content=chunk_content,
                file_path=file_path,
                start_line=start_line + 1,
                end_line=end_line,
                dependencies=list(dependencies.imports | dependencies.functions | dependencies.classes),
                priority=0.5,
                metadata={
                    'chunk_index': chunk_index,
                    'strategy': 'sliding_window',
                    'overlap_lines': overlap_lines,
                    'estimated_tokens': self._estimate_token_count(chunk_content)
                }
            )
            
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start_line = end_line - overlap_lines
            chunk_index += 1
            
            # Avoid infinite loops
            if start_line >= end_line - overlap_lines:
                break
        
        self.logger.debug(f"Created {len(chunks)} sliding window chunks for {file_path}")
        return chunks
    
    def _estimate_lines_per_chunk(self) -> int:
        """Estimate number of lines per chunk based on token limit."""
        # Rough estimation: average 50 characters per line, 4 characters per token
        avg_tokens_per_line = 50 // 4
        return self.config.chunk_size // avg_tokens_per_line


class SemanticChunker(BaseChunker):
    """Semantic chunker that breaks code at logical boundaries."""
    
    def chunk_code(self, code: str, file_path: Path) -> List[CodeChunk]:
        """Chunk code at semantic boundaries (functions, classes, etc.)."""
        chunks = []
        
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            
            # Extract top-level elements
            elements = []
            for node in tree.body:
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                element_type = type(node).__name__
                
                elements.append({
                    'node': node,
                    'start_line': start_line,
                    'end_line': end_line,
                    'type': element_type
                })
            
            # Group elements into chunks
            current_chunk_elements = []
            current_chunk_size = 0
            
            for element in elements:
                element_size = self._estimate_element_size(element, lines)
                
                # If adding this element would exceed chunk size, finalize current chunk
                if (current_chunk_size + element_size > self.config.chunk_size and 
                    current_chunk_elements):
                    
                    chunk = self._create_chunk_from_elements(
                        current_chunk_elements, lines, file_path, len(chunks)
                    )
                    chunks.append(chunk)
                    
                    current_chunk_elements = []
                    current_chunk_size = 0
                
                current_chunk_elements.append(element)
                current_chunk_size += element_size
            
            # Handle remaining elements
            if current_chunk_elements:
                chunk = self._create_chunk_from_elements(
                    current_chunk_elements, lines, file_path, len(chunks)
                )
                chunks.append(chunk)
            
            # If no semantic chunks were created, fall back to sliding window
            if not chunks:
                self.logger.warning(f"No semantic chunks created for {file_path}, falling back to sliding window")
                fallback_chunker = SlidingWindowChunker(self.config)
                chunks = fallback_chunker.chunk_code(code, file_path)
        
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}, falling back to sliding window: {e}")
            fallback_chunker = SlidingWindowChunker(self.config)
            chunks = fallback_chunker.chunk_code(code, file_path)
        
        self.logger.debug(f"Created {len(chunks)} semantic chunks for {file_path}")
        return chunks
    
    def _estimate_element_size(self, element: Dict[str, Any], lines: List[str]) -> int:
        """Estimate the token size of a code element."""
        start_line = element['start_line'] - 1  # Convert to 0-based
        end_line = element['end_line']
        
        element_lines = lines[start_line:end_line]
        element_content = '\n'.join(element_lines)
        
        return self._estimate_token_count(element_content)
    
    def _create_chunk_from_elements(
        self, 
        elements: List[Dict[str, Any]], 
        lines: List[str], 
        file_path: Path, 
        chunk_index: int
    ) -> CodeChunk:
        """Create a chunk from a list of elements."""
        if not elements:
            raise ChunkingError("Cannot create chunk from empty elements list")
        
        start_line = min(elem['start_line'] for elem in elements)
        end_line = max(elem['end_line'] for elem in elements)
        
        chunk_lines = lines[start_line - 1:end_line]  # Convert to 0-based indexing
        chunk_content = '\n'.join(chunk_lines)
        
        chunk_id = self._generate_chunk_id(file_path, start_line, end_line)
        dependencies = self._extract_dependencies(chunk_content)
        
        # Calculate priority based on element types
        priority = self._calculate_chunk_priority(elements)
        
        return CodeChunk(
            id=chunk_id,
            content=chunk_content,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            dependencies=list(dependencies.imports | dependencies.functions | dependencies.classes),
            priority=priority,
            metadata={
                'chunk_index': chunk_index,
                'strategy': 'semantic',
                'element_count': len(elements),
                'element_types': [elem['type'] for elem in elements],
                'estimated_tokens': self._estimate_token_count(chunk_content)
            }
        )
    
    def _calculate_chunk_priority(self, elements: List[Dict[str, Any]]) -> float:
        """Calculate priority for a chunk based on its elements."""
        priority_weights = {
            'ClassDef': 0.8,
            'FunctionDef': 0.7,
            'AsyncFunctionDef': 0.7,
            'If': 0.5,
            'For': 0.5,
            'While': 0.5,
            'Try': 0.6,
            'With': 0.5,
            'Import': 0.3,
            'ImportFrom': 0.3,
            'Assign': 0.4
        }
        
        if not elements:
            return 0.5
        
        total_weight = sum(priority_weights.get(elem['type'], 0.5) for elem in elements)
        return min(1.0, total_weight / len(elements))


class DependencyAwareChunker(BaseChunker):
    """Chunker that considers code dependencies for intelligent grouping."""
    
    def chunk_code(self, code: str, file_path: Path) -> List[CodeChunk]:
        """Chunk code while preserving dependency relationships."""
        chunks = []
        
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(tree)
            
            # Group related code elements
            element_groups = self._group_by_dependencies(dependency_graph)
            
            # Create chunks from groups
            for group_index, group in enumerate(element_groups):
                chunk = self._create_chunk_from_group(group, lines, file_path, group_index)
                if chunk:
                    chunks.append(chunk)
            
            # If no dependency-aware chunks were created, fall back to semantic chunking
            if not chunks:
                self.logger.warning(f"No dependency-aware chunks created for {file_path}, falling back to semantic")
                fallback_chunker = SemanticChunker(self.config)
                chunks = fallback_chunker.chunk_code(code, file_path)
        
        except Exception as e:
            self.logger.warning(f"Dependency analysis failed for {file_path}, falling back to semantic: {e}")
            fallback_chunker = SemanticChunker(self.config)
            chunks = fallback_chunker.chunk_code(code, file_path)
        
        self.logger.debug(f"Created {len(chunks)} dependency-aware chunks for {file_path}")
        return chunks
    
    def _build_dependency_graph(self, tree: ast.AST) -> Dict[str, Set[str]]:
        """Build a dependency graph from AST."""
        graph = {}
        current_context = None
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                current_context = node.name
                graph[current_context] = set()
            
            elif isinstance(node, ast.Name) and current_context:
                if isinstance(node.ctx, ast.Load):
                    graph[current_context].add(node.id)
            
            elif isinstance(node, ast.Call) and current_context:
                if isinstance(node.func, ast.Name):
                    graph[current_context].add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        graph[current_context].add(node.func.value.id)
        
        return graph
    
    def _group_by_dependencies(self, dependency_graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Group code elements by their dependencies."""
        groups = []
        visited = set()
        
        for element in dependency_graph:
            if element not in visited:
                group = self._find_connected_elements(element, dependency_graph, visited)
                groups.append(group)
        
        return groups
    
    def _find_connected_elements(
        self, 
        start_element: str, 
        dependency_graph: Dict[str, Set[str]], 
        visited: Set[str]
    ) -> List[str]:
        """Find all elements connected to the start element."""
        group = []
        stack = [start_element]
        
        while stack:
            element = stack.pop()
            if element not in visited:
                visited.add(element)
                group.append(element)
                
                # Add dependencies
                if element in dependency_graph:
                    for dep in dependency_graph[element]:
                        if dep in dependency_graph and dep not in visited:
                            stack.append(dep)
        
        return group
    
    def _create_chunk_from_group(
        self, 
        group: List[str], 
        lines: List[str], 
        file_path: Path, 
        group_index: int
    ) -> Optional[CodeChunk]:
        """Create a chunk from a dependency group."""
        # This is a simplified implementation
        # In production, you'd need to find the actual line ranges for each element
        
        if not group:
            return None
        
        # For now, create a chunk that includes all lines (simplified)
        # In a real implementation, you'd map group elements to their line ranges
        chunk_content = '\n'.join(lines)
        
        if not chunk_content.strip():
            return None
        
        chunk_id = self._generate_chunk_id(file_path, 1, len(lines))
        dependencies = self._extract_dependencies(chunk_content)
        
        return CodeChunk(
            id=chunk_id,
            content=chunk_content,
            file_path=file_path,
            start_line=1,
            end_line=len(lines),
            dependencies=list(dependencies.imports | dependencies.functions | dependencies.classes),
            priority=0.7,  # Higher priority for dependency-aware chunks
            metadata={
                'chunk_index': group_index,
                'strategy': 'dependency_aware',
                'group_elements': group,
                'estimated_tokens': self._estimate_token_count(chunk_content)
            }
        )


class PriorityChunker(BaseChunker):
    """Chunker that prioritizes important code sections."""
    
    def __init__(self, config: Configuration):
        super().__init__(config)
        self.error_patterns = [
            r'def\s+test_',  # Test functions
            r'class\s+\w*Test',  # Test classes
            r'if\s+__name__\s*==\s*["\']__main__["\']',  # Main execution blocks
            r'async\s+def',  # Async functions
            r'@\w+',  # Decorators
        ]
    
    def chunk_code(self, code: str, file_path: Path) -> List[CodeChunk]:
        """Chunk code with priority-based ordering."""
        # First, get semantic chunks
        semantic_chunker = SemanticChunker(self.config)
        chunks = semantic_chunker.chunk_code(code, file_path)
        
        # Assign priorities to chunks
        for chunk in chunks:
            chunk.priority = self._calculate_priority(chunk.content)
        
        # Sort chunks by priority (highest first)
        chunks.sort(key=lambda x: x.priority, reverse=True)
        
        # Update metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'priority_rank': i + 1,
                'strategy': 'priority',
                'original_strategy': chunk.metadata.get('strategy', 'semantic')
            })
        
        self.logger.debug(f"Created {len(chunks)} priority-ordered chunks for {file_path}")
        return chunks
    
    def _calculate_priority(self, content: str) -> float:
        """Calculate priority score for code content."""
        priority = 0.5  # Base priority
        
        # Check for important patterns
        for pattern in self.error_patterns:
            if re.search(pattern, content, re.MULTILINE):
                priority += 0.1
        
        # Check for error-prone constructs
        if 'try:' in content or 'except' in content:
            priority += 0.15
        
        if 'async' in content or 'await' in content:
            priority += 0.1
        
        # Check for complex logic
        complexity_indicators = ['if', 'elif', 'else', 'for', 'while', 'with']
        complexity_count = sum(content.count(indicator) for indicator in complexity_indicators)
        priority += min(0.2, complexity_count * 0.05)
        
        # Check for potential security issues
        security_indicators = ['eval', 'exec', 'open', 'subprocess', 'os.system']
        if any(indicator in content for indicator in security_indicators):
            priority += 0.2
        
        return min(1.0, priority)


class ContextManager:
    """Manages code context and chunking for AI processing."""
    
    def __init__(self):
        self.logger = get_logger("context")
        self.cache_manager = get_cache_manager()
        self.config = get_config()
        
        # Initialize chunkers
        self.chunkers = {
            ChunkingStrategy.SLIDING_WINDOW: SlidingWindowChunker(self.config),
            ChunkingStrategy.SEMANTIC: SemanticChunker(self.config),
            ChunkingStrategy.DEPENDENCY_AWARE: DependencyAwareChunker(self.config),
            ChunkingStrategy.PRIORITY: PriorityChunker(self.config)
        }
    
    def create_context(
        self, 
        file_path: Path, 
        strategy: Optional[ChunkingStrategy] = None,
        max_chunks: Optional[int] = None
    ) -> CodeContext:
        """Create code context for processing."""
        if strategy is None:
            strategy = self.config.chunking_strategy
        
        # Check cache first
        file_mtime = file_path.stat().st_mtime
        cache_key = self.cache_manager.get_context_cache_key(str(file_path), f"{strategy}_{max_chunks}")
        
        cached_context = self.cache_manager.get_cached_context(cache_key)
        if cached_context:
            # Verify cache is still valid
            if cached_context.file_info.get('mtime') == file_mtime:
                self.logger.debug(f"Using cached context for {file_path}")
                return cached_context
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            raise ChunkingError(f"Failed to read file {file_path}: {e}")
        
        # Validate file size
        if len(code.encode()) > self.config.max_file_size:
            raise ChunkingError(f"File {file_path} exceeds maximum size limit")
        
        # Get appropriate chunker
        chunker = self.chunkers.get(strategy)
        if not chunker:
            self.logger.warning(f"Unknown chunking strategy {strategy}, using semantic")
            chunker = self.chunkers[ChunkingStrategy.SEMANTIC]
        
        # Create chunks
        chunks = chunker.chunk_code(code, file_path)
        
        # Limit number of chunks if specified
        if max_chunks and len(chunks) > max_chunks:
            # Keep highest priority chunks
            chunks.sort(key=lambda x: x.priority, reverse=True)
            chunks = chunks[:max_chunks]
            self.logger.info(f"Limited chunks to {max_chunks} for {file_path}")
        
        # Extract overall dependencies
        dependencies = self._extract_file_dependencies(code)
        
        # Create file info
        file_info = {
            'path': str(file_path),
            'size': len(code.encode()),
            'lines': len(code.split('\n')),
            'mtime': file_mtime,
            'encoding': 'utf-8'
        }
        
        # Create context
        context = CodeContext(
            chunks=chunks,
            dependencies=dependencies,
            file_info=file_info,
            metadata={
                'strategy': strategy,
                'chunk_count': len(chunks),
                'total_tokens': sum(chunk.metadata.get('estimated_tokens', 0) for chunk in chunks)
            }
        )
        
        # Cache context
        self.cache_manager.cache_context(cache_key, context)
        
        self.logger.info(f"Created context for {file_path}: {len(chunks)} chunks using {strategy} strategy")
        return context
    
    def _extract_file_dependencies(self, code: str) -> DependencyInfo:
        """Extract comprehensive dependency information from code."""
        dependencies = DependencyInfo()
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.imports.add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.imports.add(node.module)
                    if node.names:
                        for alias in node.names:
                            dependencies.imports.add(alias.name)
                
                elif isinstance(node, ast.FunctionDef):
                    dependencies.functions.add(node.name)
                
                elif isinstance(node, ast.AsyncFunctionDef):
                    dependencies.functions.add(node.name)
                
                elif isinstance(node, ast.ClassDef):
                    dependencies.classes.add(node.name)
                
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    dependencies.variables.add(node.id)
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        dependencies.external_calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            dependencies.external_calls.add(f"{node.func.value.id}.{node.func.attr}")
        
        except SyntaxError:
            # Continue with empty dependencies if parsing fails
            pass
        
        return dependencies
    
    def merge_contexts(self, contexts: List[CodeContext]) -> CodeContext:
        """Merge multiple code contexts into one."""
        if not contexts:
            raise ChunkingError("Cannot merge empty context list")
        
        if len(contexts) == 1:
            return contexts[0]
        
        # Merge chunks
        all_chunks = []
        for context in contexts:
            all_chunks.extend(context.chunks)
        
        # Merge dependencies
        merged_dependencies = DependencyInfo()
        for context in contexts:
            merged_dependencies.imports.update(context.dependencies.imports)
            merged_dependencies.functions.update(context.dependencies.functions)
            merged_dependencies.classes.update(context.dependencies.classes)
            merged_dependencies.variables.update(context.dependencies.variables)
            merged_dependencies.external_calls.update(context.dependencies.external_calls)
        
        # Merge file info
        merged_file_info = {
            'paths': [context.file_info['path'] for context in contexts],
            'total_size': sum(context.file_info['size'] for context in contexts),
            'total_lines': sum(context.file_info['lines'] for context in contexts),
            'files_count': len(contexts)
        }
        
        # Create merged metadata
        merged_metadata = {
            'merged_contexts': len(contexts),
            'total_chunks': len(all_chunks),
            'strategies': list(set(context.metadata.get('strategy', 'unknown') for context in contexts)),
            'total_tokens': sum(context.metadata.get('total_tokens', 0) for context in contexts)
        }
        
        return CodeContext(
            chunks=all_chunks,
            dependencies=merged_dependencies,
            file_info=merged_file_info,
            metadata=merged_metadata
        )
    
    def get_chunker_stats(self) -> Dict[str, Any]:
        """Get statistics about chunker usage."""
        return {
            'available_strategies': list(self.chunkers.keys()),
            'default_strategy': self.config.chunking_strategy,
            'chunk_size': self.config.chunk_size,
            'overlap_ratio': self.config.overlap_ratio
        }


# Global context manager instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def initialize_context_manager() -> ContextManager:
    """Initialize the global context manager."""
    global _context_manager
    _context_manager = ContextManager()
    return _context_manager
