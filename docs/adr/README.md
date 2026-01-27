# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the FinPilot project.

## What are ADRs?

An Architectural Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## Template

Use the [ADR template](0000-template.md) when creating new records.

## Index

| # | Title | Status | Date |
|---|-------|--------|------|
| 0001 | [Migrate from Pickle to JSON](0001-pickle-to-json.md) | Accepted | 2025-01-15 |
| 0002 | [JWT-Based Authentication](0002-jwt-authentication.md) | Accepted | 2025-01-15 |
| 0003 | [Prometheus Metrics Integration](0003-prometheus-metrics.md) | Accepted | 2025-01-20 |
| 0004 | [Sentry Error Tracking](0004-sentry-integration.md) | Accepted | 2025-01-20 |
| 0005 | [Modular Component Architecture](0005-component-architecture.md) | Accepted | 2025-01-18 |

## Process

1. Copy `0000-template.md` to `NNNN-title.md`
2. Fill in the template
3. Submit for review via PR
4. Update index in this README
