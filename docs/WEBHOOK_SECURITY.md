# Webhook Security Best Practices

**Purpose:** Security guidelines and best practices for webhook endpoints  
**Created/Updated:** 2025-12-17  
**Agent:** GPT-5.2

## Authentication

### Bearer Token Authentication

**Recommended:** Use Bearer token authentication for all webhook endpoints.

```bash
Authorization: Bearer <token>
```

**Best Practices:**
- Use strong, randomly generated tokens (minimum 32 characters)
- Store tokens in secrets management system (AWS Secrets Manager, etc.)
- Rotate tokens regularly (every 90 days recommended)
- Use different tokens per environment (dev, staging, prod)
- Revoke tokens immediately if compromised

### Token Generation

```bash
# Generate secure token
openssl rand -hex 32

# Or using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Token Storage

Store tokens in:
- AWS Secrets Manager (production)
- Environment variables (development)
- Never commit tokens to version control
- Use `.gitignore` for local config files

## Network Security

### Network Isolation

**Production:**
- Deploy webhook endpoints in private subnets
- Use load balancer or API gateway for public access
- Restrict direct access to n8n instances
- Use VPC security groups to limit access

**Development:**
- Use localhost binding by default
- Only expose externally when necessary
- Use VPN or SSH tunnel for remote access

### Firewall Rules

**Recommended Rules:**
- Allow only from known source IPs (if possible)
- Block all public internet access to n8n instances
- Use security groups (AWS) or firewall rules (GCP/Azure)
- Log all blocked connection attempts

## Rate Limiting

### Implementation

**At Load Balancer/API Gateway:**
- Limit requests per IP: 100/minute
- Limit requests per API key: 1000/minute
- Burst limit: 20 requests/second
- Return 429 Too Many Requests when exceeded

**At Application Level:**
- Implement rate limiting middleware
- Use Redis or similar for distributed rate limiting
- Log rate limit violations for security monitoring

### Rate Limit Headers

Include rate limit information in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

## Input Validation

### Schema Validation

**Always validate:**
- Event structure matches Event Schema v1
- Required fields are present
- Field types are correct
- Field values are within expected ranges

**Implementation:**
- Use `shared/js_snippets/validate_payload.js`
- Validate against `shared/schemas/event.schema.json`
- Reject invalid payloads with 400 Bad Request

### Payload Size Limits

**Recommended Limits:**
- Maximum payload size: 1MB
- Reject larger payloads with 413 Payload Too Large
- Log oversized payload attempts

### Sanitization

**Sanitize:**
- String inputs to prevent injection attacks
- URL parameters
- File uploads (if supported)
- Never trust client input

## Logging and Monitoring

### Security Event Logging

**Log the following:**
- All authentication failures (401)
- Rate limit violations (429)
- Invalid payload attempts (400)
- Unauthorized access attempts
- Unusual traffic patterns

**Log Format:**
```json
{
  "timestamp": "2025-12-17T12:00:00Z",
  "event": "webhook_auth_failure",
  "ip": "192.168.1.1",
  "event_type": "contact.created",
  "reason": "invalid_token"
}
```

### Monitoring

**Monitor:**
- Authentication failure rates
- Rate limit violations
- Unusual request patterns
- Geographic access patterns
- Request volume anomalies

**Alerts:**
- Spike in authentication failures
- Sustained rate limit violations
- Requests from unexpected IPs
- Unusual payload sizes

## HTTPS/TLS

### SSL/TLS Requirements

**Production:**
- Always use HTTPS
- Use valid SSL certificates from trusted CAs
- Enforce TLS 1.2 or higher
- Disable weak cipher suites
- Use HSTS headers

**Certificate Management:**
- Rotate certificates before expiration
- Use automated certificate renewal (Let's Encrypt, etc.)
- Monitor certificate expiration
- Have backup certificates ready

### Certificate Validation

**Client-side:**
- Always verify server certificates
- Don't disable certificate validation
- Use certificate pinning for critical endpoints

## Webhook Registry Security

### Access Control

**Database Access:**
- Limit database access to n8n application only
- Use read-only database user for monitoring
- Audit all database access

**Registry Management:**
- Restrict who can modify webhook_registry
- Use GitOps for registry changes
- Require approval for production changes
- Log all registry modifications

### Registry Validation

**Validate:**
- Event type names (prevent injection)
- Workflow names exist in n8n
- Required payload fields are valid
- Schema types are recognized

## Incident Response

### Compromised Token

**Immediate Actions:**
1. Revoke compromised token immediately
2. Generate new token
3. Update all systems using old token
4. Review logs for unauthorized access
5. Notify security team

### DDoS Attack

**Response:**
1. Enable rate limiting (if not already)
2. Block attacking IPs at firewall/load balancer
3. Scale infrastructure if needed
4. Monitor for ongoing attacks
5. Document incident

### Data Breach

**Response:**
1. Isolate affected systems
2. Preserve logs for investigation
3. Notify affected parties
4. Conduct security audit
5. Implement additional safeguards

## Security Checklist

- [ ] Bearer token authentication implemented
- [ ] Tokens stored in secrets management
- [ ] Tokens rotated regularly
- [ ] Network isolation configured
- [ ] Firewall rules restrict access
- [ ] Rate limiting enabled
- [ ] Input validation implemented
- [ ] Payload size limits enforced
- [ ] Security events logged
- [ ] Monitoring and alerts configured
- [ ] HTTPS/TLS enforced
- [ ] Certificates managed properly
- [ ] Registry access controlled
- [ ] Incident response plan documented

## References

- Webhook Dispatch: `docs/WEBHOOK_DISPATCH.md`
- Troubleshooting: `docs/WEBHOOK_TROUBLESHOOTING.md`
- Secrets Strategy: `docs/SECRETS_STRATEGY.md`
- n8n Configuration: `docs/N8N_CONFIGURATION.md`
