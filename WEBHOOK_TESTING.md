# Webhook Testing Guide

This guide shows how to test the webhook functionality of the newear hook system.

## Files Created

1. **`webhook_test_server.py`** - Simple HTTP server that prints webhook data with "python server echo" prefix
2. **`test_webhook.py`** - Test script to validate the webhook server
3. **`test_webhook_hook.py`** - Test script to validate the webhook hook functionality
4. **`config-webhook-test.yaml`** - Configuration file for testing webhooks

## Quick Start

### 1. Start the Webhook Test Server

```bash
python3 webhook_test_server.py
```

This will start a server on `http://localhost:8080` that:
- Accepts POST requests with JSON data
- Prints received data with "python server echo" prefix
- Returns success responses
- Provides a health check endpoint

### 2. Test the Server

In another terminal:

```bash
python3 test_webhook.py
```

This validates that the server is working correctly.

### 3. Test the Webhook Hook

```bash
python3 test_webhook_hook.py
```

This tests the webhook hook functionality directly.

### 4. Test with Real Transcription

Use the webhook test configuration:

```bash
# Make sure the webhook server is running first
python3 webhook_test_server.py

# In another terminal, run newear with webhook config
python3 -m newear --config config-webhook-test.yaml
```

## Expected Output

When transcription occurs, you should see output like:

**On the webhook server:**
```
python server echo: [0.95] Hello world, this is a test
  └── chunk: 1, timestamp: 1705234567.123
```

**On the newear client:**
```
📝 [0.95] Hello world, this is a test
```

## Configuration

The webhook hook can be configured in your `config.yaml`:

```yaml
hooks:
  enabled: true
  hooks:
    - type: "webhook"
      enabled: true
      config:
        url: "http://localhost:8080"
        timeout: 10
        headers:
          Content-Type: "application/json"
          User-Agent: "newear-webhook"
```

## Webhook Payload Format

The webhook receives JSON data with this structure:

```json
{
  "text": "Transcribed text",
  "confidence": 0.95,
  "chunk_index": 1,
  "timestamp": 1705234567.123
}
```

## Advanced Usage

### Custom Port

Run the server on a different port:

```bash
python3 webhook_test_server.py 9000
```

### Multiple Hooks

You can combine webhooks with other hooks:

```yaml
hooks:
  enabled: true
  hooks:
    - type: "webhook"
      enabled: true
      config:
        url: "http://localhost:8080"
    - type: "console_log"
      enabled: true
    - type: "translation"
      enabled: true
      config:
        target_language: "es"
        service: "command"
        command: "echo 'Translated: {text}'"
```

## Troubleshooting

### Server Not Responding

- Check if the server is running: `curl http://localhost:8080`
- Verify the port is not in use: `lsof -i :8080`
- Check firewall settings

### Webhook Timeouts

- Increase timeout in configuration
- Check network connectivity
- Verify the webhook URL is correct

### Permission Errors

- Ensure Python has network permissions
- Check if the port requires root access (ports < 1024)

## Production Considerations

This test server is for development only. For production:

1. Use a proper web framework (Flask, FastAPI, etc.)
2. Add authentication and rate limiting
3. Use HTTPS for secure communication
4. Implement proper error handling and logging
5. Consider using a message queue for reliability