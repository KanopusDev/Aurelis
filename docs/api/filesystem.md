# Filesystem API

## Overview

The Filesystem API provides secure file system operations for code analysis, manipulation, and workspace management within the Aurelis platform.

## Endpoints

### List Directory Contents

**GET** `/api/v1/filesystem/list`

Lists files and directories in the specified path.

#### Query Parameters

- `path` (required): Directory path to list
- `recursive` (optional): Include subdirectories (default: false)
- `include_hidden` (optional): Include hidden files (default: false)
- `filter` (optional): File extension filter (e.g., "py,js,ts")

#### Response

```json
{
  "success": true,
  "path": "/workspace/project",
  "items": [
    {
      "name": "main.py",
      "type": "file",
      "size": 1024,
      "modified": "2025-06-17T10:30:00Z",
      "permissions": "rw-r--r--",
      "extension": "py"
    },
    {
      "name": "src",
      "type": "directory",
      "size": 4096,
      "modified": "2025-06-17T09:15:00Z",
      "permissions": "rwxr-xr-x",
      "items_count": 15
    }
  ],
  "total_items": 2,
  "total_size": 5120
}
```

### Read File Content

**GET** `/api/v1/filesystem/read`

Reads the content of a specified file.

#### Query Parameters

- `path` (required): File path to read
- `encoding` (optional): File encoding (default: utf-8)
- `lines` (optional): Specific line range (e.g., "1-50")

#### Response

```json
{
  "success": true,
  "path": "/workspace/project/main.py",
  "content": "#!/usr/bin/env python3\n...",
  "encoding": "utf-8",
  "size": 1024,
  "lines": 42,
  "language": "python"
}
```

### Write File Content

**POST** `/api/v1/filesystem/write`

Creates or updates a file with the specified content.

#### Request Body

```json
{
  "path": "/workspace/project/new_file.py",
  "content": "print('Hello, World!')",
  "encoding": "utf-8",
  "create_directories": true,
  "backup": false
}
```

#### Response

```json
{
  "success": true,
  "path": "/workspace/project/new_file.py",
  "size": 20,
  "created": true,
  "backup_path": null
}
```

### Create Directory

**POST** `/api/v1/filesystem/mkdir`

Creates a new directory.

#### Request Body

```json
{
  "path": "/workspace/project/new_dir",
  "recursive": true,
  "permissions": "755"
}
```

#### Response

```json
{
  "success": true,
  "path": "/workspace/project/new_dir",
  "created": true
}
```

### Delete File/Directory

**DELETE** `/api/v1/filesystem/delete`

Deletes a file or directory.

#### Query Parameters

- `path` (required): Path to delete
- `recursive` (optional): Delete directory recursively (default: false)
- `backup` (optional): Create backup before deletion (default: false)

#### Response

```json
{
  "success": true,
  "path": "/workspace/project/old_file.py",
  "deleted": true,
  "backup_path": "/backups/old_file.py.bak"
}
```

### Move/Rename File

**POST** `/api/v1/filesystem/move`

Moves or renames a file or directory.

#### Request Body

```json
{
  "source": "/workspace/project/old_name.py",
  "destination": "/workspace/project/new_name.py",
  "overwrite": false,
  "backup": true
}
```

#### Response

```json
{
  "success": true,
  "source": "/workspace/project/old_name.py",
  "destination": "/workspace/project/new_name.py",
  "moved": true,
  "backup_path": "/backups/new_name.py.bak"
}
```

### Copy File/Directory

**POST** `/api/v1/filesystem/copy`

Copies a file or directory.

#### Request Body

```json
{
  "source": "/workspace/project/source.py",
  "destination": "/workspace/project/copy.py",
  "recursive": true,
  "preserve_permissions": true,
  "overwrite": false
}
```

#### Response

```json
{
  "success": true,
  "source": "/workspace/project/source.py",
  "destination": "/workspace/project/copy.py",
  "copied": true,
  "size": 1024
}
```

### Search Files

**GET** `/api/v1/filesystem/search`

Searches for files matching specified criteria.

#### Query Parameters

- `query` (required): Search query (filename pattern or content)
- `path` (optional): Search root path (default: workspace root)
- `type` (optional): Search type ("name|content|both") (default: name)
- `case_sensitive` (optional): Case-sensitive search (default: false)
- `regex` (optional): Use regex patterns (default: false)
- `include_extensions` (optional): File extensions to include
- `exclude_extensions` (optional): File extensions to exclude

#### Response

```json
{
  "success": true,
  "query": "test",
  "matches": [
    {
      "path": "/workspace/project/test_main.py",
      "type": "file",
      "match_type": "filename",
      "line_matches": [],
      "size": 512,
      "modified": "2025-06-17T10:30:00Z"
    },
    {
      "path": "/workspace/project/utils.py",
      "type": "file",
      "match_type": "content",
      "line_matches": [
        {
          "line_number": 15,
          "line_content": "def test_function():",
          "match_start": 4,
          "match_end": 8
        }
      ],
      "size": 2048,
      "modified": "2025-06-17T09:45:00Z"
    }
  ],
  "total_matches": 2,
  "search_time_ms": 150
}
```

### Get File Information

**GET** `/api/v1/filesystem/info`

Retrieves detailed information about a file or directory.

#### Query Parameters

- `path` (required): Path to analyze
- `include_content_stats` (optional): Include content analysis (default: false)

#### Response

```json
{
  "success": true,
  "path": "/workspace/project/main.py",
  "type": "file",
  "size": 1024,
  "created": "2025-06-15T14:20:00Z",
  "modified": "2025-06-17T10:30:00Z",
  "accessed": "2025-06-17T10:35:00Z",
  "permissions": "rw-r--r--",
  "owner": "user",
  "group": "staff",
  "extension": "py",
  "mime_type": "text/x-python",
  "encoding": "utf-8",
  "content_stats": {
    "lines": 42,
    "blank_lines": 8,
    "comment_lines": 12,
    "code_lines": 22,
    "language": "python",
    "complexity": "medium"
  }
}
```

### Watch File Changes

**POST** `/api/v1/filesystem/watch`

Sets up file system watching for changes.

#### Request Body

```json
{
  "path": "/workspace/project",
  "recursive": true,
  "events": ["create", "modify", "delete", "move"],
  "include_patterns": ["*.py", "*.js"],
  "exclude_patterns": ["*.pyc", "node_modules/*"],
  "webhook_url": "https://your-app.com/webhook/file-changes"
}
```

#### Response

```json
{
  "success": true,
  "watch_id": "watch_12345",
  "path": "/workspace/project",
  "active": true,
  "created_at": "2025-06-17T10:30:00Z"
}
```

### Stop File Watching

**DELETE** `/api/v1/filesystem/watch/{watch_id}`

Stops file system watching.

#### Response

```json
{
  "success": true,
  "watch_id": "watch_12345",
  "stopped": true
}
```

## Security Features

### Path Validation

All file operations include automatic path validation to prevent:
- Directory traversal attacks
- Access to system files
- Operations outside workspace boundaries

### Permission Checks

Every operation verifies:
- Read/write permissions
- File ownership
- Workspace access rights

### File Type Restrictions

Certain operations are restricted for:
- Binary files (limited read operations)
- System files
- Hidden configuration files

## Error Handling

### Common Error Codes

- `400`: Invalid file path or parameters
- `403`: Permission denied
- `404`: File or directory not found
- `409`: File already exists (when overwrite=false)
- `413`: File too large
- `422`: Unsupported file type or encoding
- `500`: Filesystem operation failed

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Access denied to the specified path",
    "details": {
      "path": "/restricted/file.txt",
      "required_permission": "read",
      "suggestion": "Check file permissions or workspace access rights"
    }
  }
}
```

## Rate Limiting

- **Read Operations**: 1000 requests per minute
- **Write Operations**: 100 requests per minute
- **Search Operations**: 50 requests per minute
- **Watch Operations**: 10 concurrent watches per API key

## Examples

### List Python Files

```bash
curl -X GET "https://api.aurelis.dev/v1/filesystem/list?path=/workspace&filter=py&recursive=true" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Read File Content

```bash
curl -X GET "https://api.aurelis.dev/v1/filesystem/read?path=/workspace/main.py" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Create New File

```bash
curl -X POST "https://api.aurelis.dev/v1/filesystem/write" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/workspace/new_module.py",
    "content": "def hello_world():\n    print(\"Hello, World!\")",
    "create_directories": true
  }'
```

### Search for Functions

```bash
curl -X GET "https://api.aurelis.dev/v1/filesystem/search?query=def%20.*test.*&type=content&regex=true" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Integration

### Python SDK

```python
from aurelis import FilesystemClient

fs = FilesystemClient(api_key="your_api_key")

# List directory contents
files = fs.list_directory("/workspace", recursive=True, filter="py")

# Read file
content = fs.read_file("/workspace/main.py")

# Write file
fs.write_file("/workspace/new_file.py", "print('Hello')")

# Search files
results = fs.search("test", type="content", include_extensions=["py"])
```

### CLI Integration

```bash
# List files
aurelis fs list /workspace --recursive --filter=py

# Read file
aurelis fs read /workspace/main.py

# Write file
aurelis fs write /workspace/new_file.py "print('Hello')"

# Search
aurelis fs search "test" --type=content --extensions=py
```

## Best Practices

1. **Path Handling**: Always use absolute paths and validate input
2. **Error Handling**: Implement proper error handling for all operations
3. **Performance**: Use filters and pagination for large directory listings
4. **Security**: Never expose sensitive files or system paths
5. **Backups**: Enable backups for destructive operations
6. **Monitoring**: Use file watching for real-time change detection

## Limitations

- Maximum file size: 100MB
- Maximum directory depth: 20 levels
- Maximum concurrent watches: 10 per API key
- Supported encodings: UTF-8, ASCII, Latin-1
- Binary file operations are limited

## Webhook Events

When using file watching, webhook events are sent in this format:

```json
{
  "watch_id": "watch_12345",
  "event": "modify",
  "path": "/workspace/main.py",
  "timestamp": "2025-06-17T10:30:00Z",
  "details": {
    "old_size": 1024,
    "new_size": 1100,
    "checksum": "abc123def456"
  }
}
```
