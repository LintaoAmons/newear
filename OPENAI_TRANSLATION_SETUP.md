# OpenAI Translation Hook Setup Guide

This guide explains how to set up and use the OpenAI translation hook to automatically translate transcribed text to Chinese (or any other language).

## 🚀 Quick Start

### 1. Get OpenAI API Key

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 2. Set Environment Variable

```bash
export OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Test the Hook

```bash
uv run python3 test_openai_translation.py
```

### 4. Use with Newear

**OpenAI Direct:**
```bash
uv run newear --config config-openai-translation.yaml
```

**OpenRouter:**
```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
uv run newear --config config-openrouter-translation.yaml
```

## 📝 Configuration

### Basic Configuration (OpenAI Direct)

```yaml
hooks:
  enabled: true
  hooks:
    - type: "openai_translation"
      enabled: true
      config:
        api_key: "${OPENAI_API_KEY}"  # Use environment variable
        target_language: "Chinese"
        model: "gpt-3.5-turbo"
        max_tokens: 1000
        temperature: 0.3
        print_translation: true
```

### OpenRouter Configuration

```yaml
hooks:
  enabled: true
  hooks:
    - type: "openai_translation"
      enabled: true
      config:
        api_key: "${OPENROUTER_API_KEY}"  # OpenRouter API key
        base_url: "https://openrouter.ai/api/v1"
        target_language: "Chinese"
        model: "openai/gpt-3.5-turbo"  # Note the provider prefix
        max_tokens: 1000
        temperature: 0.3
        print_translation: true
```

### Advanced Configuration

```yaml
hooks:
  enabled: true
  hooks:
    - type: "openai_translation"
      enabled: true
      config:
        api_key: "${OPENAI_API_KEY}"
        target_language: "Chinese (Simplified)"
        model: "gpt-4"  # Use GPT-4 for better quality
        max_tokens: 2000
        temperature: 0.1  # Lower temperature for more consistent translations
        print_translation: true
    
    # Also log original text
    - type: "console_log"
      enabled: true
      config:
        show_confidence: true
    
    # Save both original and translated text
    - type: "file_append"
      enabled: true
      config:
        file_path: "translations.log"
        format: "Original: {text}"
```

## 🌍 Supported Languages

You can translate to any language supported by OpenAI. Examples:

- `"Chinese"` or `"Chinese (Simplified)"` or `"中文"`
- `"Spanish"` or `"Español"`
- `"French"` or `"Français"`
- `"Japanese"` or `"日本語"`
- `"German"` or `"Deutsch"`
- `"Korean"` or `"한국어"`

## 🌐 Supported Providers

### OpenAI (Direct)
- **API Key**: Get from [OpenAI](https://platform.openai.com/api-keys)
- **Base URL**: Default (no need to specify)
- **Models**: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`

### OpenRouter
- **API Key**: Get from [OpenRouter](https://openrouter.ai/keys)
- **Base URL**: `https://openrouter.ai/api/v1`
- **Models**: `openai/gpt-3.5-turbo`, `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.1-8b-instruct`

### Other Compatible Providers
Any provider that supports the OpenAI API format can be used by setting the `base_url`.

## 🔧 Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `api_key` | API key for the provider | Required |
| `base_url` | Custom API base URL | null (uses OpenAI default) |
| `target_language` | Target language for translation | "Chinese" |
| `model` | Model to use | "gpt-3.5-turbo" |
| `max_tokens` | Maximum tokens for translation | 1000 |
| `temperature` | Response randomness (0.0-1.0) | 0.3 |
| `print_translation` | Print translation to console | true |
| `output_prefix` | Prefix for translation output | "" (no prefix) |

## 🎯 Expected Output

When running newear with OpenAI translation, you'll see:

**Default (no prefix):**
```
📝 [0.95] Hello world, this is a test
[Chinese] 你好世界，这是一个测试
```

**With custom prefix (e.g., `output_prefix: "🤖"`):**
```
📝 [0.95] Hello world, this is a test
🤖 [Chinese] 你好世界，这是一个测试
```

The first line shows the original transcription with confidence score, and the second line shows the AI translation with optional prefix.

### 🎨 Customizing Output Prefix

You can customize the prefix for translation output:

```yaml
# No prefix (default)
output_prefix: ""

# Robot emoji
output_prefix: "🤖"

# Text prefix
output_prefix: "AI:"

# Custom prefix
output_prefix: "Translation:"
```

## 💰 Cost Considerations

### OpenAI Direct Pricing
- GPT-3.5-turbo: ~$0.001 per 1k tokens
- GPT-4: ~$0.03 per 1k tokens
- GPT-4-turbo: ~$0.01 per 1k tokens

### OpenRouter Pricing
- GPT-3.5-turbo: ~$0.001 per 1k tokens
- Claude 3.5 Sonnet: ~$0.003 per 1k tokens
- Llama 3.1 8B: ~$0.0001 per 1k tokens

### Usage Notes
- Short phrases typically use 10-50 tokens
- Monitor usage at [OpenAI Usage](https://platform.openai.com/usage) or [OpenRouter Usage](https://openrouter.ai/usage)
- OpenRouter often offers competitive pricing and access to multiple models

## 🛠️ Troubleshooting

### API Key Issues

```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### Common Errors

1. **"OpenAI API key not configured"**
   - Set the `OPENAI_API_KEY` environment variable
   - Or add `api_key` directly to config (not recommended)

2. **"OpenAI library not installed"**
   - Run: `uv add openai`

3. **"Rate limit exceeded"**
   - Add delays between requests
   - Upgrade your OpenAI plan

4. **"Invalid API key"**
   - Check that your API key is correct
   - Ensure it starts with `sk-`

## 🔐 Security Best Practices

1. **Use environment variables** for API keys
2. **Never commit API keys** to version control
3. **Set usage limits** in OpenAI dashboard
4. **Monitor API usage** regularly
5. **Use least privilege** API keys

## 📊 Performance Tips

1. **Use gpt-3.5-turbo** for faster, cheaper translations
2. **Lower temperature** (0.1-0.3) for consistent results
3. **Batch processing** for multiple translations
4. **Cache translations** to avoid duplicate API calls

## 🔄 Multiple Language Support

You can set up multiple translation hooks:

```yaml
hooks:
  enabled: true
  hooks:
    - type: "openai_translation"
      enabled: true
      config:
        api_key: "${OPENAI_API_KEY}"
        target_language: "Chinese"
        print_translation: true
    
    - type: "openai_translation"
      enabled: true
      config:
        api_key: "${OPENAI_API_KEY}"
        target_language: "Spanish"
        print_translation: true
```

## 🎉 Ready to Use!

Once configured, the OpenAI translation hook will automatically translate every transcribed chunk in real-time, perfect for:

- **Live translation** during meetings
- **Language learning** with instant feedback
- **Content creation** in multiple languages
- **Accessibility** for multilingual audiences