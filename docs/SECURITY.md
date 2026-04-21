# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ---------------- |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you find a security vulnerability in OKO, please report it responsibly:

1. **DO NOT** create a public GitHub issue
2. Email the maintainer directly
3. Include as much detail as possible

We aim to respond within 48 hours.

## Security Considerations

### Data Storage

- OKO stores error data in SQLite (`oko.db`)
- Ensure the database file has appropriate file permissions
- In production, store the database in a secured directory

### Credentials

- **Never** commit credentials or tokens to version control
- Use environment variables for sensitive configuration:
  ```python
  import os
  oko.init(
      telegram_token=os.environ.get("TELEGRAM_TOKEN"),
      telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID"),
  )
  ```

### Network Security

- When using WebhookConnector, use HTTPS in production
- Consider networkfirewall rules for SQLite file access
- Dashboard should be behind authentication in production

### Rate Limiting

- Default rate limit: 10 events per burst
- Adjust based on your traffic:
  ```python
  oko.init(
      rate_limit_max=5.0,      # Reduce if getting too many notifications
      rate_limit_refill=0.5,    # Slower refill rate
  )
  ```

### Input Validation

OKO does not perform deep input validation on error messages. 
When displaying errors in Dashboard, ensure your template engine 
escapes output (OKO uses Jinja2 with autoescaping by default).

### Dependencies

Keep dependencies updated:
```bash
pip install --upgrade oko
```

Check for known vulnerabilities:
```bash
pip-audit
```

## Best Practices

1. **Use environment variables** for secrets
2. **Restrict Dashboard access** in production
3. **Monitor disk usage** for SQLite database
4. **Set retention policy**: `retention_days=7` (default: 7 days)
5. **Use HTTPS** for webhook endpoints