# Purpose: Prometheus integration documentation for n8n automation platform
# Created/Updated: 2025-11-20
# Agent: BACKEND_AGENT

# Prometheus Integration Guide

## Overview

The Automation Hub exports metrics to Prometheus for observability and monitoring. All workflows log events and metrics that are collected by Prometheus and visualized in Grafana.

## Metric Export Architecture

```
n8n Workflows → log_event workflow → Prometheus Push Gateway → Prometheus → Grafana
```

## Required Metrics

### Workflow Metrics

#### workflow_success_total
- **Type:** Counter
- **Description:** Total number of successful workflow executions
- **Labels:**
  - `workflow_name`: Name of the workflow
  - `domain`: Workflow domain (crm, infra, meta, shared)
  - `env`: Environment (dev, staging, prod)
- **Example:** `workflow_success_total{workflow_name="lead_intake",domain="crm",env="prod"}`

#### workflow_failure_total
- **Type:** Counter
- **Description:** Total number of failed workflow executions
- **Labels:**
  - `workflow_name`: Name of the workflow
  - `domain`: Workflow domain
  - `env`: Environment
  - `error_type`: Type of error (optional)
- **Example:** `workflow_failure_total{workflow_name="lead_intake",domain="crm",env="prod",error_type="ValidationError"}`

#### workflow_duration_seconds
- **Type:** Histogram
- **Description:** Workflow execution duration in seconds
- **Labels:**
  - `workflow_name`: Name of the workflow
  - `domain`: Workflow domain
  - `env`: Environment
- **Buckets:** [0.1, 0.5, 1, 5, 10, 30, 60, 300]

### Infrastructure Metrics

#### infra_deploy_latency_ms
- **Type:** Histogram
- **Description:** Infrastructure deployment latency in milliseconds
- **Labels:**
  - `deployment_type`: Type of deployment (terraform, kubernetes, etc.)
  - `environment`: Target environment
  - `status`: Deployment status
- **Buckets:** [100, 500, 1000, 5000, 10000, 30000, 60000]

#### infra_deploy_success_total
- **Type:** Counter
- **Description:** Total successful infrastructure deployments
- **Labels:**
  - `deployment_type`: Type of deployment
  - `environment`: Target environment

#### infra_deploy_failure_total
- **Type:** Counter
- **Description:** Total failed infrastructure deployments
- **Labels:**
  - `deployment_type`: Type of deployment
  - `environment`: Target environment
  - `error_type`: Type of error

### Error Handler Metrics

#### error_handler_total
- **Type:** Counter
- **Description:** Total errors handled by error handler workflow
- **Labels:**
  - `severity`: Error severity (low, medium, high, critical)
  - `workflow_name`: Workflow that generated the error

#### error_handler_success_total
- **Type:** Counter
- **Description:** Total errors successfully handled
- **Labels:**
  - `severity`: Error severity
  - `workflow_name`: Workflow that generated the error

### Incident Metrics

#### incident_total
- **Type:** Counter
- **Description:** Total incidents created
- **Labels:**
  - `severity`: Incident severity
  - `source`: Source system
  - `status`: Incident status

## Metric Export Implementation

### From n8n Workflows

Workflows use the `log_event` workflow to export metrics:

```javascript
// In n8n Code node
const event = {
  id: generateUUID(),
  type: "workflow.execution.completed",
  source: "n8n",
  env: "prod",
  timestamp: new Date().toISOString(),
  correlation_id: $workflow.correlationId,
  payload: {
    workflow_name: $workflow.name,
    status: "success",
    duration_ms: $workflow.executionTime
  }
};

// Call log_event workflow
await $http.post('/webhook/log-event', event);
```

### Prometheus Push Gateway

Metrics are pushed to Prometheus Push Gateway:

- **Endpoint:** Configured in `shared/config/environments.{env}.yaml`
- **Path:** `/metrics/job/{job_name}`
- **Method:** POST
- **Format:** Prometheus exposition format

### Metric Collection Points

1. **Workflow Execution:** Metrics exported at workflow start/end
2. **Error Handling:** Metrics exported when errors occur
3. **Infrastructure Deployments:** Metrics exported during deployment lifecycle
4. **Health Checks:** Metrics exported during health check execution

## Configuration

### Environment Configuration

Metrics endpoints are configured in environment YAML files:

```yaml
external_services:
  prometheus:
    endpoint: "https://prometheus.automation-hub.example.com"
    metrics_path: "/api/v1/query"
```

### n8n Configuration

n8n workflows must be configured to:
1. Call `log_event` workflow for metric export
2. Include correlation IDs for tracing
3. Export metrics in Prometheus format

## Alerting Rules

### Critical Alerts

- **Workflow Success Rate < 90%:** Alert when workflow success rate drops below 90%
- **Critical Errors:** Alert on any critical severity errors
- **Infrastructure Deployment Failures:** Alert on deployment failures

### Warning Alerts

- **Workflow Success Rate < 95%:** Warning when success rate drops below 95%
- **High Error Rate:** Alert when error rate exceeds threshold
- **Slow Deployments:** Alert when deployment latency exceeds threshold

## Grafana Dashboards

See `docs/grafana-dashboards/` for dashboard JSON files:
- `workflow-health.json`: Workflow health and success rates
- `error-rates.json`: Error rates and incident tracking
- `infra-metrics.json`: Infrastructure deployment metrics

## Integration with log_event Workflow

The `log_event` workflow:
1. Receives event payloads from workflows
2. Validates event schema
3. Exports metrics to Prometheus Push Gateway
4. Logs events with correlation IDs
5. Handles export failures gracefully

## Best Practices

1. **Always include correlation_id:** Enables tracing across workflows
2. **Use appropriate metric types:** Counters for totals, histograms for durations
3. **Label consistently:** Use standard label names across all metrics
4. **Export on critical events:** Success, failure, and key milestones
5. **Handle export failures:** Metrics export should not block workflow execution

## Troubleshooting

### Metrics Not Appearing

1. Check Prometheus endpoint configuration
2. Verify network connectivity to Prometheus
3. Check log_event workflow execution
4. Review Prometheus Push Gateway logs

### High Metric Volume

1. Review metric export frequency
2. Consider metric aggregation
3. Check for duplicate metric exports
4. Review Prometheus retention policies

## References

- Prometheus Documentation: https://prometheus.io/docs/
- Prometheus Push Gateway: https://github.com/prometheus/pushgateway
- Grafana Dashboard Import: https://grafana.com/docs/grafana/latest/dashboards/manage-dashboards/

