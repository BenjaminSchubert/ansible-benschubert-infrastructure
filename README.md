# ansible-benschubert-infrastructure

[![Docs](https://github.com/BenjaminSchubert/ansible-benschubert-infrastructure/actions/workflows/docs.yml/badge.svg)](https://benjaminschubert.github.io/ansible-benschubert-infrastructure/)
[![ci](https://github.com/BenjaminSchubert/ansible-benschubert-infrastructure/actions/workflows/ci.yml/badge.svg)](https://github.com/BenjaminSchubert/ansible-benschubert-infrastructure/actions/workflows/ci.yml)
![GitHub License](https://img.shields.io/github/license/BenjaminSchubert/ansible-benschubert-infrastructure)
![Static Badge](https://img.shields.io/badge/Status-Experimental-red)


This is an ansible collection to setup some base services for a web stack.

The focus of this project is towards a single-node deployment, where everything
runs in rootless podman containers on the same machine.

## Services installed

- [Traefik](https://traefik.io/) to act as an ingress controller
- [Authentik](https://goauthentik.io/) to handle SSO
- [Grafana](https://grafana.com/) for viewing metrics and logs
- [Mimir](https://grafana.com/oss/mimir/) to ingest logs and metrics, and provide an [AlertManager](https://prometheus.io/docs/alerting/latest/alertmanager/) deployment
- [Loki](https://grafana.com/oss/loki/) to store logs and handle alerts based on logs
- [Grafana Alloy](https://grafana.com/oss/alloy-opentelemetry-collector/) to publish metrics and logs
