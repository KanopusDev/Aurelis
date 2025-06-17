# Interactive Shell Guide

The Aurelis Interactive Shell provides a powerful command-line interface for working with AI-powered code analysis and generation using GitHub models.

## Starting the Shell

```bash
aurelis shell
```

or with a custom configuration:

```bash
aurelis shell --config /path/to/config.yaml
```

## Shell Features

### Core Features

- **Rich Interactive Prompt**: Enhanced command-line interface with syntax highlighting
- **Auto-completion**: Intelligent completion for commands, file paths, and options
- **Command History**: Persistent command history across sessions
- **Session Management**: Save and restore shell sessions
- **Context Awareness**: Maintains working directory and file context

### Enhanced Experience

When `prompt_toolkit` is installed, the shell provides:
- Advanced auto-completion with context awareness
- Syntax highlighting for commands
- Key bindings (Ctrl+C, Ctrl+D)
- History-based suggestions

## Available Commands

### File Analysis

#### `analyze <file_path>`
Analyze code files for issues, performance, and security vulnerabilities.

```bash
aurelis:myproject> analyze src/main.py
```

Features:
- Syntax analysis
- Logic error detection
- Performance bottlenecks
- Security vulnerabilities
- Code style issues

#### `explain <file_path> [--level=beginner|intermediate|advanced]`
Get detailed explanations of code functionality.

```bash
aurelis:myproject> explain utils.py --level=beginner
```

### Code Generation

#### `generate <description> [--language=python] [--output=file.py]`
Generate code from natural language descriptions.

```bash
aurelis:myproject> generate "Create a REST API endpoint for user authentication"
aurelis:myproject> generate "Sort algorithm implementation" --language=python
```

### Code Improvement

#### `fix <file_path>`
Auto-fix detected code issues.

```bash
aurelis:myproject> fix src/buggy_code.py
```

#### `refactor <file_path>`
Get refactoring suggestions for cleaner, more maintainable code.

```bash
aurelis:myproject> refactor legacy_module.py
```

#### `test <file_path>`
Generate comprehensive tests for code files.

```bash
aurelis:myproject> test src/calculator.py
```

#### `docs <file_path>`
Generate documentation for code files.

```bash
aurelis:myproject> docs src/api.py
```

### Navigation and File Operations

#### `cd <directory>`
Change the current working directory.

```bash
aurelis:myproject> cd src/
aurelis:src> cd ../tests/
```

#### `ls [directory]`
List files and directories.

```bash
aurelis:myproject> ls
aurelis:myproject> ls src/
```

#### `pwd`
Show current working directory.

```bash
aurelis:myproject> pwd
/home/user/myproject
```

#### `cat <file_path>`
Display file contents.

```bash
aurelis:myproject> cat README.md
```

### Search and Discovery

#### `search <query>`
Search through codebase for patterns, functions, or text.

```bash
aurelis:myproject> search "authentication"
aurelis:myproject> search "def calculate"
```

### Configuration and System

#### `config [key] [value]`
View or modify configuration settings.

```bash
aurelis:myproject> config                    # Show all settings
aurelis:myproject> config models.primary     # Show specific setting
aurelis:myproject> config models.primary gpt-4o  # Set setting
```

#### `status`
Show system status and component health.

```bash
aurelis:myproject> status
```

#### `models`
List available AI models and their capabilities.

```bash
aurelis:myproject> models
aurelis:myproject> models list
aurelis:myproject> models test codestral-2501
```

#### `tools`
List available analysis and generation tools.

```bash
aurelis:myproject> tools
```

### Session Management

#### `session <command>`
Manage shell sessions.

```bash
aurelis:myproject> session info           # Show current session info
aurelis:myproject> session save my-work  # Save current session
aurelis:myproject> session load my-work  # Load saved session
aurelis:myproject> session list          # List saved sessions
aurelis:myproject> session clear         # Clear current session
```

### Utility Commands

#### `history`
Show command history.

```bash
aurelis:myproject> history
```

#### `clear`
Clear the screen and redisplay welcome message.

```bash
aurelis:myproject> clear
```

#### `help [command]`
Show help information.

```bash
aurelis:myproject> help
aurelis:myproject> help analyze
aurelis:myproject> help generate
```

#### `exit` or `quit`
Exit the shell (saves session automatically).

```bash
aurelis:myproject> exit
```

## Context Management

The shell maintains context about your current work:

- **Current File**: The last file you analyzed or worked with
- **Working Directory**: Your current location in the filesystem  
- **Project Root**: Automatically detected project root directory
- **Session Variables**: Custom variables for your workflow

### Context Indicators

The prompt shows contextual information:

```bash
aurelis:myproject>                    # Basic prompt
aurelis:myproject(main.py)>          # Current file context
aurelis:src(utils.py)>               # Directory and file context
```

## Auto-completion

The shell provides intelligent auto-completion for:

### Commands
Type partial command names and press Tab:
```bash
aurelis:myproject> an<Tab>
analyze
```

### File Paths
Navigate and complete file paths:
```bash
aurelis:myproject> analyze src/<Tab>
src/main.py    src/utils.py    src/models/
```

### Command Options
Complete command-specific options:
```bash
aurelis:myproject> config <Tab>
show    set    get    models    cache    security
```

## Tips and Best Practices

### Efficient Workflow

1. **Start with Analysis**: Use `analyze` to understand code quality
2. **Use Context**: Commands remember your last file automatically
3. **Save Sessions**: Use `session save` for complex workflows
4. **Leverage History**: Use arrow keys to navigate command history

### Example Workflow

```bash
# Start shell and navigate to project
aurelis shell
aurelis:~> cd my-python-project
aurelis:my-python-project> 

# Analyze the main module
aurelis:my-python-project> analyze src/main.py

# Fix any issues found
aurelis:my-python-project> fix src/main.py

# Generate tests
aurelis:my-python-project> test src/main.py

# Generate documentation
aurelis:my-python-project> docs src/main.py

# Save the session
aurelis:my-python-project> session save main-module-work
```

### Performance Tips

- Use specific file paths for faster analysis
- Keep sessions small for better performance  
- Use `status` to monitor system health
- Configure model preferences for your use case

## Troubleshooting

### Common Issues

**Shell won't start**: Check configuration and GitHub token
```bash
aurelis config
```

**Commands fail**: Verify models are available
```bash
aurelis models
aurelis status
```

**Slow performance**: Check network connection and rate limits
```bash
aurelis status
```

### Getting Help

- Use `help <command>` for specific command help
- Use `status` to check system health  
- Check logs for detailed error information
- Verify configuration with `config` command

## Advanced Features

### Custom Prompt Styling

The shell supports rich formatting and styling. Colors and formatting are automatically applied based on:
- Command types (analysis vs generation)
- File types and languages
- Success/error status
- Context information

### Keyboard Shortcuts

- **Ctrl+C**: Interrupt current command
- **Ctrl+D**: Exit shell  
- **Up/Down**: Navigate command history
- **Tab**: Auto-complete commands and paths
- **Ctrl+R**: Search command history (when available)

### Integration with Other Tools

The shell integrates with:
- Git repositories (automatic detection)
- Python virtual environments
- IDE configurations
- Project configuration files

This comprehensive shell interface makes Aurelis a powerful companion for AI-assisted development workflows.
