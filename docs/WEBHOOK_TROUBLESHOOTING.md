# Webhook Troubleshooting Guide

**Purpose:** Common webhook issues and troubleshooting steps  
**Created/Updated:** 2025-12-17  
**Agent:** GPT-5.2

## Common Issues

### 401 Unauthorized

**Symptoms:**
- HTTP 401 response from webhook endpoint
- "Invalid API key" or "Unauthorized" error message

**Causes:**
- Missing Authorization header
- Invalid or expired API key
- Incorrect token format

**Solutions:**
1. Verify Authorization header is present:
```bash
curl -v -X POST "$WEBHOOK_URL/webhook/dispatch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"contact.created",...}'
```

2. Check token is valid and not expired
3. Verify token format: `Bearer <token>` (with space)
4. Check token has correct permissions for the environment

### 404 Not Found

**Symptoms:**
- HTTP 404 response
- "Event type not found" or "No workflow registered"

**Causes:**
- Event type not registered in webhook_registry
- Event type is inactive (`is_active=false`)
- Typo in event type name

**Solutions:**
1. Check webhook registry:
```sql
SELECT event_type, is_active, target_workflow_name
FROM public.webhook_registry
WHERE event_type = 'contact.created';
```

2. Verify event type spelling matches registry
3. Activate event type if needed:
```sql
UPDATE public.webhook_registry
SET is_active = true
WHERE event_type = 'contact.created';
```

### 400 Bad Request

**Symptoms:**
- HTTP 400 response
- Validation error messages

**Causes:**
- Missing required payload fields
- Invalid payload structure
- Schema validation failure

**Solutions:**
1. Check required fields in registry:
```sql
SELECT required_payload_fields
FROM public.webhook_registry
WHERE event_type = 'contact.created';
```

2. Verify payload structure matches Event Schema v1
3. Check validation errors in response body
4. Use webhook_dispatch_generator to see expected format

### 500 Internal Server Error

**Symptoms:**
- HTTP 500 response
- Generic server error

**Causes:**
- Database connection issues
- Workflow execution failure
- n8n instance problems

**Solutions:**
1. Check n8n health:
```bash
curl http://localhost:5678/healthz
```

2. Check database connectivity
3. Review n8n logs for errors
4. Verify workflow exists and is active in n8n

### Timeout Issues

**Symptoms:**
- Request times out
- No response received

**Causes:**
- Network connectivity issues
- n8n instance overloaded
- Workflow execution taking too long

**Solutions:**
1. Check network connectivity to n8n instance
2. Verify n8n is responsive:
```bash
curl -m 5 http://localhost:5678/healthz
```

3. Check workflow execution times
4. Consider async execution for long-running workflows

## Debugging Steps

### 1. Verify Webhook Endpoint

```bash
# Test basic connectivity
curl -v "$WEBHOOK_URL/webhook/dispatch"
```

### 2. Check Authentication

```bash
# Test with valid token
curl -X POST "$WEBHOOK_URL/webhook/dispatch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### 3. Validate Event Structure

```bash
# Use generator to create test event
node ops/scripts/webhook_dispatch_generator.js \
  --event-type contact.created \
  --target-workflow-name "Lead Intake" \
  --target-logical-id lead_intake \
  --payload-schema-type contact \
  --required email
```

### 4. Check Registry

```sql
-- List all active events
SELECT event_type, target_workflow_name, is_active
FROM public.webhook_registry
WHERE is_active = true;

-- Check specific event
SELECT * FROM public.webhook_registry
WHERE event_type = 'contact.created';
```

### 5. Review n8n Logs

```bash
# Docker logs
docker logs n8n

# Or check application logs
tail -f /var/log/n8n/n8n.log
```

## Testing Checklist

- [ ] Webhook endpoint is reachable
- [ ] Authentication token is valid
- [ ] Event type is registered in webhook_registry
- [ ] Event type is active (`is_active=true`)
- [ ] Payload contains all required fields
- [ ] Payload structure matches Event Schema v1
- [ ] Target workflow exists in n8n
- [ ] Target workflow is active
- [ ] n8n instance is healthy
- [ ] Database is accessible

## References

- Webhook Dispatch Guide: `docs/WEBHOOK_DISPATCH.md`
- n8n Webhook Guide: `docs/n8n_webhook_guide2025.md`
- Webhook Registry Schema: `ops/scripts/webhook_registry.sql`
