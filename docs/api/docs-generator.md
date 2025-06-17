# Documentation Generator API

## Overview

The Documentation Generator API provides automated documentation generation capabilities for codebases, creating comprehensive technical documentation from source code analysis.

## Endpoints

### Generate Documentation

**POST** `/api/v1/docs/generate`

Generates documentation for a specified codebase or project.

#### Request Body

```json
{
  "project_path": "string",
  "output_format": "markdown|html|pdf",
  "include_private": false,
  "documentation_types": [
    "api",
    "architecture",
    "deployment",
    "user_guide"
  ],
  "template": "default|custom",
  "custom_template_path": "string",
  "language": "auto|python|javascript|typescript|java|csharp",
  "exclude_patterns": [
    "*/tests/*",
    "*/node_modules/*"
  ]
}
```

#### Response

```json
{
  "success": true,
  "documentation_id": "doc_12345",
  "output_path": "/path/to/generated/docs",
  "generated_files": [
    {
      "type": "api",
      "path": "/path/to/api-docs.md",
      "size_bytes": 15420
    }
  ],
  "processing_time_ms": 2500,
  "warnings": []
}
```

### Get Documentation Status

**GET** `/api/v1/docs/status/{documentation_id}`

Retrieves the status of a documentation generation task.

#### Response

```json
{
  "id": "doc_12345",
  "status": "completed|processing|failed",
  "progress": 100,
  "created_at": "2025-06-17T10:30:00Z",
  "completed_at": "2025-06-17T10:32:30Z",
  "error_message": null
}
```

### List Documentation Templates

**GET** `/api/v1/docs/templates`

Retrieves available documentation templates.

#### Response

```json
{
  "templates": [
    {
      "name": "default",
      "description": "Standard technical documentation template",
      "supported_formats": ["markdown", "html", "pdf"],
      "documentation_types": ["api", "architecture", "deployment"]
    },
    {
      "name": "enterprise",
      "description": "Enterprise-grade documentation with compliance sections",
      "supported_formats": ["markdown", "html", "pdf"],
      "documentation_types": ["api", "architecture", "deployment", "security", "compliance"]
    }
  ]
}
```

### Update Documentation

**PUT** `/api/v1/docs/{documentation_id}`

Updates existing documentation with new content or regenerates based on code changes.

#### Request Body

```json
{
  "regenerate": true,
  "update_sections": ["api", "architecture"],
  "preserve_custom_content": true
}
```

#### Response

```json
{
  "success": true,
  "updated_files": [
    "/path/to/updated-api-docs.md"
  ],
  "processing_time_ms": 1500
}
```

### Delete Documentation

**DELETE** `/api/v1/docs/{documentation_id}`

Removes generated documentation and associated metadata.

#### Response

```json
{
  "success": true,
  "message": "Documentation deleted successfully"
}
```

## Configuration

### Documentation Types

- **api**: API reference documentation
- **architecture**: System architecture and design docs
- **deployment**: Deployment and infrastructure guides
- **user_guide**: End-user documentation
- **security**: Security policies and procedures
- **compliance**: Compliance and regulatory documentation

### Output Formats

- **markdown**: GitHub-flavored Markdown
- **html**: Responsive HTML with navigation
- **pdf**: Professional PDF reports

### Template Customization

Custom templates can be provided using Jinja2 syntax:

```json
{
  "template": "custom",
  "custom_template_path": "/path/to/custom-template.j2",
  "template_variables": {
    "company_name": "Aurelis",
    "version": "1.0.0",
    "author": "Development Team"
  }
}
```

## Error Handling

### Common Error Codes

- `400`: Invalid request parameters
- `404`: Documentation or template not found
- `422`: Unsupported file format or language
- `500`: Documentation generation failed

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PROJECT_PATH",
    "message": "The specified project path does not exist or is not accessible",
    "details": {
      "path": "/invalid/path",
      "suggestion": "Verify the path exists and has proper permissions"
    }
  }
}
```

## Rate Limiting

- **Documentation Generation**: 10 requests per hour per API key
- **Status Checks**: 100 requests per minute per API key
- **Template Operations**: 50 requests per minute per API key

## Examples

### Generate API Documentation

```bash
curl -X POST "https://api.aurelis.dev/v1/docs/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/workspace/my-project",
    "output_format": "markdown",
    "documentation_types": ["api", "architecture"],
    "include_private": false
  }'
```

### Check Generation Status

```bash
curl -X GET "https://api.aurelis.dev/v1/docs/status/doc_12345" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Integration

### Python SDK

```python
from aurelis import DocsGenerator

generator = DocsGenerator(api_key="your_api_key")

# Generate documentation
result = generator.generate(
    project_path="/workspace/my-project",
    output_format="markdown",
    documentation_types=["api", "architecture"]
)

# Check status
status = generator.get_status(result.documentation_id)
```

### CLI Integration

```bash
aurelis docs generate \
  --project-path /workspace/my-project \
  --output-format markdown \
  --types api,architecture \
  --template enterprise
```

## Best Practices

1. **Project Structure**: Ensure your project follows standard conventions for better documentation quality
2. **Code Comments**: Include comprehensive docstrings and comments for better API documentation
3. **Template Selection**: Choose templates that match your organization's documentation standards
4. **Regular Updates**: Set up automated documentation updates as part of your CI/CD pipeline
5. **Version Control**: Track documentation changes alongside code changes

## Limitations

- Maximum project size: 1GB
- Maximum processing time: 30 minutes
- Supported languages: Python, JavaScript, TypeScript, Java, C#, Go, Rust
- Custom templates must be valid Jinja2 syntax

## Support

For issues with documentation generation, contact support with:
- Documentation ID
- Project details
- Error messages
- Expected vs. actual output
