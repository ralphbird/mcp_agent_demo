# PagerDuty Alerting Setup for Currency API

This document explains how to set up PagerDuty alerting integration with the Currency Conversion
API monitoring system.

## Overview

The Currency API system includes comprehensive monitoring with Grafana, Prometheus, and PagerDuty
integration for alerting on critical issues and performance degradation.

## Prerequisites

1. **PagerDuty Account**: You need access to a PagerDuty account with permissions to create services
   and integrations
2. **Docker Environment**: The Currency API system running with Docker (see main README.md)
3. **Grafana Access**: Access to Grafana at <http://localhost:3000> (admin/admin)

## PagerDuty Configuration

### 1. Create PagerDuty Service

1. Log in to your PagerDuty account
2. Go to **Services** > **Service Directory**
3. Click **+ New Service**
4. Configure your service:
   - **Name**: `Currency Conversion API`
   - **Description**: `Production currency conversion service monitoring`
   - **Escalation Policy**: Select or create an appropriate escalation policy
   - **Incident Settings**: Configure as needed for your organization

### 2. Add Events API v2 Integration

1. In your new service, go to the **Integrations** tab
2. Click **+ Add Integration**
3. Select **Events API v2**
4. **Name**: `Currency API Grafana`
5. Click **Add Integration**
6. **Copy the Integration Key** - you'll need this for configuration

### 3. Optional: Create Separate Load Tester Service

If you want separate alerting for load testing issues:

1. Create another service: `Currency API Load Testing`
2. Add Events API v2 integration
3. Copy the integration key for load tester alerts

## Local Environment Setup

### 1. Create Environment File

Copy the example environment file and add your PagerDuty keys:

```bash
cp .env.example .env
```

Edit `.env` and set your PagerDuty integration keys:

```bash
# Primary PagerDuty integration key for critical alerts
PAGERDUTY_CURRENCY_APP_KEY=your-actual-integration-key-here

# Optional: Separate key for load tester alerts
PAGERDUTY_LOAD_TESTER_KEY=your-load-tester-key-here
```

### 2. Restart Grafana

Restart the monitoring stack to pick up the new configuration:

```bash
make down
make up
```

Or restart just Grafana:

```bash
docker-compose restart grafana
```

## Alert Rules Overview

The system includes pre-configured alert rules for common issues:

### Critical Alerts (Immediate PagerDuty notification)

- **API Service Down**: Service is completely unavailable
- **High Error Rate**: >5% of requests returning 5xx errors over 5 minutes
- **Database Connection Issues**: Any database connection errors

### Warning Alerts (PagerDuty notification after threshold)

- **High Response Time**: 95th percentile >1000ms for 5 minutes
- **High Request Rate**: >100 requests/second for 5 minutes
- **Load Test Failures**: >10% failure rate in load testing for 3 minutes

## Alert Configuration

### Notification Channels

Three PagerDuty notification channels are configured:

1. **pagerduty-critical**: For critical service issues
   - Immediate alerts
   - 30-second retry frequency
   - Critical severity

2. **pagerduty-warning**: For performance issues
   - 2-minute retry frequency
   - Warning severity

3. **pagerduty-load-tester**: For load testing issues
   - 5-minute retry frequency
   - Warning severity

### Customizing Alerts

Alert rules are defined in:

- `docker/grafana/provisioning/alerting/currency-api-alerts.yml`

To modify thresholds or add new alerts:

1. Edit the YAML file
2. Restart Grafana: `docker-compose restart grafana`
3. Alerts will be automatically provisioned

## Setup Process

### 1. Configure Environment Variables

Set your PagerDuty integration key in `.env`:

```bash
# Primary PagerDuty integration key for critical alerts
PAGERDUTY_CURRENCY_APP_KEY=your-actual-integration-key-here

# Optional: Separate key for load tester alerts
# If not set, will use PAGERDUTY_CURRENCY_APP_KEY
PAGERDUTY_LOAD_TESTER_KEY=your-load-tester-key-here
```

### 2. Restart Services

```bash
# Restart to load new environment variables
source .env && docker-compose restart grafana
```

### 3. Verify Contact Points

1. Open Grafana: <http://localhost:3000> (admin/admin)
2. Go to **Alerting** → **Contact Points**
3. You should see **pagerduty-critical** and **pagerduty-warning** contact points
4. If not visible, create them manually:
   - **New contact point** → **Name**: `pagerduty-critical`
   - **Type**: **PagerDuty** → **Integration Key**: Your `PAGERDUTY_CURRENCY_APP_KEY`

### 4. Verify Alert Rules

1. **Alerting** → **Alert Rules**
2. You should see working alerts:
   - **Currency API Service Down** (Critical)
   - **Currency API High Error Rate** (Critical)
   - **Currency API High Request Rate** (Warning)

## Testing the Integration

### 1. Test Real Alert (Recommended)

```bash
# Stop the API service to trigger alerts
docker-compose stop api

# Wait 60-90 seconds for alert to fire and send to PagerDuty
# Check your PagerDuty dashboard for new incident

# Restart the service to resolve alert
docker-compose start api
```

### 2. Test with PagerDuty Script (Alternative)

```bash
# Test PagerDuty API directly
set -a && source .env && set +a && poetry run python scripts/test_pagerduty.py
```

### 3. Verify in PagerDuty Dashboard

1. Check your PagerDuty dashboard
2. Verify incident was created with:
   - **Service**: Currency Conversion API
   - **Alert details**: From Grafana
   - **Auto-resolution**: When service comes back up

### 4. Check Grafana Logs

```bash
# Verify PagerDuty notifications are being sent
docker-compose logs grafana | grep -i "notifying pagerduty"
```

You should see log entries like:

```text
msg="notifying Pagerduty" event_type=trigger
```

## Alert Runbooks

Each alert includes a runbook URL placeholder. Update these in the alert configuration:

```yaml
annotations:
  runbook_url: "https://your-company-wiki.com/runbooks/api-down"
```

### Suggested Runbook Topics

- **API Service Down**: Check container health, resource usage, dependencies
- **High Error Rate**: Review logs, check database connectivity, validate recent deployments
- **High Latency**: Analyze slow queries, check resource constraints, review traffic patterns
- **Database Issues**: Check PostgreSQL health, connection limits, disk space

## Monitoring Dashboard

Access the Grafana dashboards to complement PagerDuty alerts:

- **Currency API Dashboard**: <http://localhost:3000/d/currency-api>
- **Load Testing Dashboard**: <http://localhost:3000/d/load-testing>
- **System Logs**: <http://localhost:3000/d/logs>

## Troubleshooting

### Common Issues

1. **Alerts not triggering PagerDuty**:
   - Verify `PAGERDUTY_CURRENCY_APP_KEY` is correctly set
   - Check Grafana logs: `docker-compose logs grafana`
   - Test the integration key: `set -a && source .env && set +a && poetry run python scripts/test_pagerduty.py`

2. **Too many alerts**:
   - Adjust alert thresholds in the YAML configuration
   - Increase `for` duration to require longer threshold breach
   - Review notification frequency settings

3. **Missing metrics**:
   - Ensure Prometheus is scraping metrics: <http://localhost:9090/targets>
   - Verify API is exposing metrics: <http://localhost:8000/metrics>
   - Check Prometheus configuration in `docker/prometheus.yml`

### Logs and Debugging

View relevant logs:

```bash
# Grafana logs (for alerting issues)
docker-compose logs grafana

# Prometheus logs (for metrics collection)
docker-compose logs prometheus

# API logs (for application issues)
docker-compose logs api
```

## Advanced Configuration

### Custom Alert Templates

Modify PagerDuty alert templates in:
`docker/grafana/provisioning/notifiers/pagerduty.yml`

### Additional Notification Channels

Add other notification channels (Slack, email, etc.) alongside PagerDuty:

```yaml
# Example: Add Slack notification
- name: slack-alerts
  type: slack
  settings:
    url: "https://hooks.slack.com/your-webhook-url"
    channel: "#alerts"
```

### Environment-Specific Configuration

Use different PagerDuty services for different environments:

```bash
# Production
PAGERDUTY_CURRENCY_APP_KEY=prod-integration-key

# Staging
PAGERDUTY_CURRENCY_APP_KEY=staging-integration-key
```

## Security Considerations

- **Integration Keys**: Keep PagerDuty integration keys secure
- **Environment Files**: Add `.env` to `.gitignore` (already included)
- **Access Control**: Limit Grafana admin access in production
- **Network Security**: Consider firewall rules for external notifications

## Support

For issues with:

- **PagerDuty Integration**: Check PagerDuty Events API documentation
- **Grafana Configuration**: See Grafana alerting documentation
- **Currency API Issues**: Review application logs and metrics
- **System Setup**: Refer to main README.md documentation
