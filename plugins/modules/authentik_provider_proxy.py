DOCUMENTATION = """
---
module: authentik_provider_proxy

short_description: Allows administration of Authentik proxy providers

description:
  - This module allows the administration of Authentik proxy providers via the
    Authentik API.
  - See https://docs.goauthentik.io/docs/add-secure-apps/providers/proxy/

options:
  provider:
    description:
      - The configuration for the specified provider
    type: dict
    required: true
    suboptions:
      authorization_flow:
        description:
          - The slug for the authorization flow used to authorize connecting
            to the connected application
        type: str
        required: true
      external_host:
        description:
          - The URL at which the protected application will be hosted
        type: str
        required: true
      mode:
        description:
          - The mode with which the provider operates
        type: str
        required: true
        choices:
          - forward_single
      name:
        description: The name to give to the provider
        type: str
        required: true

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Configure a provider for Traefik's dashboard
  benschubert.infrastructure.authentik_provider_proxy:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    provider:
      name: traefik-provider
      authorization_flow: only-admin-authorization
      external_host: https://traefik.test
      mode: forward_single
"""

RETURN = """
data:
  description: The information returned by the Authentik API
  returned: always
  type: dict
  sample:
    access_token_validity: hours=1
    assigned_application_name: <my application>
    assigned_application_slug: <my application slug>
    authentication_flow: null
    authorization_flow: 8ac6d32e-d6d7-487a-9262-3d16e121ad9f
    basic_auth_enabled: false
    basic_auth_password_attribute: ''
    basic_auth_user_attribute: ''
    certificate: null
    client_id: pI0UYHcvqYS2JPRvOO3KhSEeP2d0q6hnS5NJmbho
    component: ak-provider-proxy-form
    cookie_domain: ''
    external_host: https://traefik.test
    intercept_header_auth: true
    internal_host: ''
    internal_host_ssl_validation: true
    jwks_sources: []
    meta_model_name: authentik_providers_proxy.proxyprovider
    mode: forward_single
    name: Traefik's dashboard
    outpost_set:
    - Outpost authentik Embedded Outpost
    pk: 1
    property_mappings:
    - 04ff5c23-0913-44c4-b256-9e062f5a8f72
    - bccf1bab-e50f-41fa-89b0-9624ae58e1e5
    - 270683ab-b0be-4aa0-b68c-91846ba6256f
    - 30e8959e-d2b4-41c5-a1d6-72c1a4742926
    redirect_uris: |-
      https://traefik.test/outpost.goauthentik.io/callback?X-authentik-auth-callback=true
      https://traefik.test?X-authentik-auth-callback=true
    refresh_token_validity: days=30
    skip_path_regex: ''
    verbose_name: Proxy Provider
    verbose_name_plural: Proxy Providers
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["provider"] = {
        "type": "dict",
        "required": True,
        "options": {
            "name": {"type": "str", "required": True},
            "authorization_flow": {"type": "str", "required": True},
            "external_host": {"type": "str", "required": True},
            "mode": {
                "type": "str",
                "choices": ["forward_single"],
                "required": True,
            },
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    provider = module.params["provider"]
    name = provider["name"]

    execute(
        module,
        "/api/v3/providers/proxy/",
        "pk",
        {"name__iexact": name},
        provider,
        state=module.params["state"],
    )


if __name__ == "__main__":
    main()
