
import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass
import tempfile

@dataclass
class FileContext:
    path: Path
    content: str
    is_temp: bool = False

class FileManager:
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir or os.getcwd())
        self.active_files: Dict[str, FileContext] = {}
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aurelis_"))

    def attach_file(self, file_reference: str) -> Optional[FileContext]:
        """Handle file reference with # syntax"""
        clean_ref = file_reference.strip("# ")
        
        # Check if file exists in workspace
        file_path = self.workspace_dir / clean_ref
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            context = FileContext(file_path, content)
            self.active_files[clean_ref] = context
            return context

        # Create new temp file
        temp_path = self.temp_dir / clean_ref
        context = FileContext(temp_path, "", is_temp=True)
        self.active_files[clean_ref] = context
        return context

    def save_file(self, file_reference: str, content: str) -> Path:
        """Save content to file, creating if necessary"""
        clean_ref = file_reference.strip("# ")
        
        if clean_ref in self.active_files:
            file_context = self.active_files[clean_ref]
            path = file_context.path
        else:
            path = self.workspace_dir / clean_ref
            
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return path

    def get_file_content(self, file_reference: str) -> Optional[str]:
        """Get content of tracked file"""
        clean_ref = file_reference.strip("# ")
        if clean_ref in self.active_files:
            return self.active_files[clean_ref].content
        return None

    def parse_file_references(self, text: str) -> list[str]:
        """Extract file references from text"""
        return [word for word in text.split() if word.startswith('#') and len(word) > 1]

    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
