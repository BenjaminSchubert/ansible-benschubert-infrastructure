# ansible-benschubert-infrastructure

This is an ansible collection to setup some base services for a web stack.

The focus of this project is towards a single-node deployment, where everything
runs in rootless podman containers on the same machine.

## Services installed

- [Traefik](https://traefik.io/) to act as an ingress controller
- [Authentik](https://goauthentik.io/) to handle SSO
- [Grafana](https://grafana.com/) for viewing metrics and logs
