# NewsCollector Configuration Guide

This document describes the configuration system for NewsCollector, including setup, validation, and management.

## Overview

The NewsCollector configuration system provides:

- **Environment-aware configuration**: Different config files for dev/prod/test
- **Validation**: Comprehensive validation of all configuration values
- **Environment overrides**: Ability to override config with environment variables
- **Type safety**: Pydantic models for runtime validation

## Quick Start

1. **Copy the example configuration**:

   ```bash
   cp config.toml.example config.toml
   ```

2. **Edit the configuration** with your settings:

   ```bash
   nano config.toml
   ```

3. **Validate the configuration**:
   ```bash
   python manage_config.py validate
   ```

## Configuration Structure

### Global Settings (`[global]`)

```toml
[global]
# Enable or disable email notifications
email_enabled = false

# Default model to use for generating briefs
default_model = "openai-gpt4"

# Default prompt template for brief generation
prompt = """
1. **Identify Core Themes**: As you read through the articles...
2. **Synthesize Information**: Combine the insights from all articles...
"""
```

### Email Configuration (`[email]`)

```toml
[email]
# Email sender address (must be verified with your email provider)
sender = "FlashAiNews <no-reply@yourdomain.com>"

# Email recipient address
receiver = "your-email@example.com"

# Email service API key (Resend, SendGrid, etc.)
api_key = "your-email-api-key"
```

### Model Configurations (`[models.*]`)

```toml
# OpenAI GPT-4 Configuration
[models.openai-gpt4]
model = "gpt-4"
provider = "openai"
api_key = "sk-your-openai-api-key"
base_url = "https://api.openai.com/v1"

# DeepSeek Configuration
[models.deepseek-reasoner]
model = "deepseek-reasoner"
provider = "deepseek"
api_key = "sk-your-deepseek-api-key"
base_url = "https://api.deepseek.com"
```

## Environment Variables

You can override configuration values using environment variables:

```bash
# Global settings
export EMAIL_ENABLED=true
export DEFAULT_MODEL=openai-gpt4
export DEFAULT_PROMPT="Custom prompt template"

# Email settings
export EMAIL_SENDER="FlashAiNews <no-reply@yourdomain.com>"
export EMAIL_RECEIVER="your-email@example.com"
export EMAIL_API_KEY="your-email-api-key"

# Thread pool settings
export THREAD_POOL_MAX_WORKERS=8
export THREAD_POOL_NAME_PREFIX="NewsCollector"
```

## Configuration Management

### Using the Management Script

The `manage_config.py` script provides several commands for managing configuration:

```bash
# Validate current configuration
python manage_config.py validate

# Show configuration summary
python manage_config.py show

# Create default configuration
python manage_config.py create
```

### Programmatic Usage

```python
from app.config import get_config, validate_config, reload_config

# Get current configuration
config = get_config()

# Validate configuration
if validate_config():
    print("Configuration is valid")

# Force reload configuration
config = reload_config()

# Get specific model configuration
from app.config import get_model_config
model_config = get_model_config("openai-gpt4")
```

## Environment-Specific Configuration

The system automatically selects the appropriate configuration file based on the `ENV` environment variable:

- **Development** (`ENV=dev` or not set): `config.toml`
- **Production** (`ENV=prod`): `/app/config.toml`
- **Testing** (`ENV=test`): `config.toml`

## Validation

The configuration system validates:

1. **Required fields**: All required configuration fields must be present
2. **Data types**: Values must match expected types
3. **Email format**: Email addresses must be valid
4. **Model providers**: Provider names must be valid
5. **Model references**: Default model must exist in configuration
6. **API keys**: API keys must not be empty

### Validation Errors

Common validation errors and solutions:

```
❌ Configuration validation failed: Model 'openai-gpt4' missing required field: api_key
```

**Solution**: Add the missing `api_key` field to the model configuration.

```
❌ Configuration validation failed: Invalid provider 'invalid-provider' for model 'test-model'
```

**Solution**: Use a valid provider: `openai`, `deepseek`, or `gemini`.

```
❌ Configuration validation failed: Default model 'missing-model' not found
```

**Solution**: Either add the missing model configuration or change the default model.

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **File Permissions**: Ensure configuration files have appropriate permissions
3. **Environment Variables**: Use environment variables for sensitive data in production

## Troubleshooting

### Configuration Not Found

```
❌ Configuration file not found: /app/config.toml
```

**Solution**: Ensure the configuration file exists at the expected path for your environment.

### Invalid TOML

```
❌ Invalid TOML configuration: Expected '=' after key
```

**Solution**: Check the TOML syntax in your configuration file.

### Missing Dependencies

```
❌ ModuleNotFoundError: No module named 'pydantic'
```

**Solution**: Install required dependencies:

```bash
pip install pydantic
```

## Advanced Configuration

### Custom Validation

You can add custom validation by extending the Pydantic models:

```python
from app.models.config import GlobalConfigModel
from pydantic import validator

class CustomGlobalConfig(GlobalConfigModel):
    @validator('prompt')
    def validate_prompt_length(cls, v):
        if len(v) < 10:
            raise ValueError('Prompt must be at least 10 characters long')
        return v
```

### Configuration Hooks

You can add custom logic when configuration is loaded:

```python
from app.config import get_config

def on_config_loaded(config):
    # Custom logic here
    pass

config = get_config()
on_config_loaded(config)
```

## API Reference

### Configuration Functions

- `get_config()`: Get current configuration
- `load_config(reload=False)`: Load configuration with optional reload
- `reload_config()`: Force reload configuration
- `validate_config()`: Validate configuration without loading
- `get_model_config(model_name=None)`: Get specific model configuration

### Email Functions

- `init_email(config)`: Initialize email service
- `validate_email_config(config)`: Validate email configuration
- `is_email_initialized()`: Check if email is initialized

### Thread Pool Functions

- `init_thread_pool(max_workers=None)`: Initialize thread pool
- `get_thread_pool()`: Get thread pool instance
- `shutdown_thread_pool()`: Shutdown thread pool
- `get_thread_pool_stats()`: Get thread pool statistics

### Utility Functions

- `create_default_config()`: Create default configuration template
- `get_config_summary(config)`: Get configuration summary
