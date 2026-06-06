# ADR 0006 - Dedicated Observability Environment

## Status

Accepted

## Context

CanTelcoX is moving from a modular monolith toward independently deployable services. Operational visibility must remain separate from business services so the monitoring plane can continue to observe failures even when application containers are unhealthy.

The current services expose `/health` endpoints but do not yet expose Prometheus application metrics.

## Decision

Deploy an observability stack in a dedicated environment named `cantelcox-observability`.

For the lab, this environment can be an LXC container, a VM, or a dedicated Linux host. The project does not require a specific virtualization platform.

The observability environment contains the monitoring code and configuration. The application microservices run on separate VMs and are linked from Prometheus target configuration.

The initial stack contains:

- Prometheus for metric storage and scraping.
- Blackbox Exporter for HTTP health probes.
- Grafana for dashboards.

The stack is defined in `infrastructure/observability/docker-compose.yml` and is deployed with Docker Compose. Microservice VM endpoints are listed in `infrastructure/observability/prometheus/targets/microservices.yml`.

## Consequences

- Observability can be operated independently from the application stack.
- Health monitoring works immediately through existing `/health` endpoints.
- Service-level metrics require a later application instrumentation step, for example exposing `/metrics` in each FastAPI service.
- Network reachability between the observability environment and application services must be maintained.
