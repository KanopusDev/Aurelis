# Contributing to Aurelis

## Welcome Contributors

Thank you for your interest in contributing to Aurelis! This guide will help you get started with contributing to our AI-powered code analysis and generation platform.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and follow our code of conduct:

- **Be respectful**: Treat all community members with respect and kindness
- **Be inclusive**: Welcome newcomers and help them get started
- **Be collaborative**: Work together to improve the project
- **Be constructive**: Provide helpful feedback and suggestions
- **Be professional**: Keep discussions focused on the project

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.9 or higher
- Git version control
- A GitHub account
- Basic understanding of async/await patterns
- Familiarity with type hints and Pydantic

### Development Environment Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/kanopusdev/aurelis.git
   cd aurelis
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run tests to verify setup**
   ```bash
   pytest tests/
   ```

## Development Workflow

### Branching Strategy

We follow the GitHub Flow branching model:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature development branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Critical production fixes

### Creating a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes and commit
git add .
git commit -m "feat: add new feature"

# Push to your fork
git push origin feature/your-feature-name
```

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(models): add support for new GitHub model
fix(cache): resolve cache invalidation issue
docs(api): update API documentation for v1.2
test(analyzer): add unit tests for code analysis
```

## Types of Contributions

### Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Detailed steps to reproduce the bug
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: Python version, OS, Aurelis version
6. **Logs**: Relevant error messages or logs

**Bug Report Template:**
```markdown
## Bug Description
Brief description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11.0]
- Aurelis: [e.g., 1.2.0]

## Additional Context
Any other context about the problem.
```

### Feature Requests

For feature requests, please provide:

1. **Problem description**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches you've considered
4. **Use cases**: Real-world scenarios where this would be useful

### Code Contributions

#### Areas for Contribution

1. **Core Features**
   - Model orchestration improvements
   - New analysis capabilities
   - Performance optimizations

2. **Integrations**
   - New IDE integrations
   - Additional AI model providers
   - Third-party tool integrations

3. **Developer Experience**
   - CLI improvements
   - Documentation enhancements
   - Error handling improvements

4. **Testing & Quality**
   - Unit test coverage
   - Integration tests
   - Performance benchmarks

#### Code Style Guidelines

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

**Configuration files:**
- `pyproject.toml`: Main configuration
- `.flake8`: Flake8 configuration
- `mypy.ini`: MyPy configuration

**Running quality checks:**
```bash
# Format code
black aurelis/ tests/
isort aurelis/ tests/

# Lint code
flake8 aurelis/ tests/

# Type checking
mypy aurelis/

# Run all checks
pre-commit run --all-files
```

#### Testing Guidelines

1. **Unit Tests**
   - Test individual functions and classes
   - Use mocking for external dependencies
   - Aim for >90% code coverage

2. **Integration Tests**
   - Test component interactions
   - Use real services when possible
   - Test error scenarios

3. **Example Test Structure:**
```python
import pytest
from unittest.mock import Mock, patch
from aurelis.models import ModelOrchestrator, ModelRequest, TaskType

class TestModelOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return ModelOrchestrator()
    
    @pytest.fixture
    def sample_request(self):
        return ModelRequest(
            prompt="Test prompt",
            task_type=TaskType.CODE_GENERATION
        )
    
    async def test_process_request_success(self, orchestrator, sample_request):
        # Arrange
        with patch('aurelis.models.github_client') as mock_client:
            mock_client.generate.return_value = "Generated code"
            
            # Act
            result = await orchestrator.process_request(sample_request)
            
            # Assert
            assert result.content == "Generated code"
            assert result.success is True
    
    async def test_process_request_failure(self, orchestrator, sample_request):
        # Test error handling
        with patch('aurelis.models.github_client') as mock_client:
            mock_client.generate.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                await orchestrator.process_request(sample_request)
```

### Documentation Contributions

We welcome improvements to documentation:

1. **API Documentation**
   - Update docstrings
   - Add usage examples
   - Improve type hints

2. **User Guides**
   - Installation instructions
   - Configuration guides
   - Best practices

3. **Developer Documentation**
   - Architecture overviews
   - Development setup
   - Contributing guidelines

**Documentation Standards:**
- Use Markdown for documentation files
- Follow the existing structure and style
- Include code examples where applicable
- Test code examples to ensure they work

## Review Process

### Pull Request Guidelines

1. **Before submitting:**
   - Ensure all tests pass
   - Run code quality checks
   - Update documentation if needed
   - Add tests for new functionality

2. **Pull Request Template:**
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Criteria

Reviewers will check for:

1. **Functionality**: Does the code work as intended?
2. **Quality**: Is the code well-written and maintainable?
3. **Testing**: Are there adequate tests?
4. **Documentation**: Is documentation updated?
5. **Performance**: Are there performance implications?
6. **Security**: Are there security considerations?

### Feedback Process

1. **Address feedback**: Respond to reviewer comments
2. **Make changes**: Update code based on feedback
3. **Re-request review**: Ask for another review after changes
4. **Merge**: Maintainers will merge when approved

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat (link in README)
- **Email**: maintainers@aurelis.dev

### Getting Help

If you need help:

1. Check existing documentation
2. Search GitHub issues
3. Ask in GitHub Discussions
4. Join our Discord community

### Recognition

We appreciate all contributions! Contributors are recognized through:

- GitHub contributor list
- Release notes acknowledgments
- Special recognition for significant contributions

## Development Guidelines

### Architecture Principles

1. **Modularity**: Keep components loosely coupled
2. **Async/Await**: Use async patterns for I/O operations
3. **Type Safety**: Use comprehensive type hints
4. **Error Handling**: Implement robust error handling
5. **Testing**: Write tests for all new code
6. **Documentation**: Document all public APIs

### Performance Considerations

- Use async/await for I/O operations
- Implement caching where appropriate
- Consider memory usage for large operations
- Profile performance-critical code
- Use connection pooling for external services

### Security Guidelines

- Never commit API keys or secrets
- Validate all user inputs
- Use secure defaults
- Follow security best practices
- Consider security implications of changes

## Release Process

### Version Management

We follow [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

### Release Workflow

1. **Feature freeze**: Stop adding new features
2. **Testing**: Comprehensive testing of release candidate
3. **Documentation**: Update documentation
4. **Release notes**: Prepare release notes
5. **Run release script**: Execute `python scripts/release.py [patch|minor|major]`
   - This updates version in pyproject.toml
   - Creates git tag and commit
   - Prompts to push changes to GitHub
   - Can create a GitHub Release
6. **GitHub Release**: Create release via GitHub UI or CLI
7. **PyPI Publishing**: Automated via GitHub Actions workflow
8. **Deploy**: Deploy to production environments

### PyPI Publishing

We use GitHub Actions to automatically publish releases to PyPI:

1. Create and publish a new GitHub Release
2. The `publish-pypi.yml` workflow triggers automatically
3. Package is built using Poetry and uploaded to PyPI
4. Verify the package is available at https://pypi.org/p/aurelisai

To modify the publishing process:
- Edit `.github/workflows/publish-pypi.yml`
- Configure PyPI trusted publishing in the GitHub repository settings

## Questions?

If you have questions about contributing:

1. Check this guide first
2. Look at existing issues and PRs
3. Ask in GitHub Discussions
4. Contact maintainers directly

Thank you for contributing to Aurelis! Your contributions help make AI-powered development tools better for everyone.

## Quick Reference

### Useful Commands

```bash
# Set up development environment
poetry install

# Run tests
poetry run pytest tests/
poetry run pytest tests/ -v --cov=aurelis

# Code quality
poetry run black aurelis/ tests/
poetry run isort aurelis/ tests/
poetry run ruff aurelis/ tests/

# Run all checks
poetry run pre-commit run --all-files

# Start development server
poetry run aurelis serve --debug

# Build documentation
cd docs/
poetry run make html

# Build package locally
poetry build

# Check package
poetry run twine check dist/*

# Bump version (patch, minor, major)
poetry version patch
```

### File Structure

```
aurelis/
├── aurelis/           # Main package
│   ├── core/         # Core functionality
│   ├── models/       # Model orchestration
│   ├── api/          # API endpoints
│   ├── cli/          # Command-line interface
│   └── shell/        # Interactive shell
├── tests/            # Test suite
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── .github/          # GitHub workflows
└── pyproject.toml    # Project configuration
```

### Links

- [Project Repository](https://github.com/aurelis/aurelis)
- [Issue Tracker](https://github.com/aurelis/aurelis/issues)
- [Discussions](https://github.com/aurelis/aurelis/discussions)
- [Documentation](https://docs.aurelis.dev)
- [Discord Community](https://discord.gg/aurelis)
