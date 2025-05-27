DOCUMENTATION = """
---
module: authentik_provider_oauth2

short_description: Allows administration of Authentik OAuth2 providers

description:
  - This module allows the administration of Authentik Oauth2 providers via the
    Authentik API.
  - See https://docs.goauthentik.io/docs/add-secure-apps/providers/oauth2/

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
      invalidation_flow:
        description:
          - The slug for the invalidation flow used to invalidate a session
        type: str
        required: true
      name:
        description: The name to give to the provider
        type: str
        required: true
      redirect_uris:
        description:
          - The URIs that are valid redirection targets after login.
          - "This must be a dictionary of the form {url: <url>, matching_mode: 'strict' or 'regex'}"
        type: list
        elements: dict
        required: true
      property_mappings:
        description:
          - The ids of the scopes to give to this application.
          - See M(benschubert.infrastructure.authentik_propertymappings_scope_info)
            for how to retrieve scopes by name more easily
        type: list
        elements: str
        required: true
      signing_key:
        description:
          - The primary key of the signing key to use for signing those entries
        type: str
        required: true

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Configure a provider for Grafana
  benschubert.infrastructure.authentik_provider_oauth2:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    provider:
      name: grafana-
      authorization_flow: only-admin-authorization
      redirect_uris:
        - url: https://grafana.test/login/generic_oauth
          matching_mode: strict
      property_mappings:
        - <email_mapping>.pk
        - <openid_mapping>.pk
        - <profile_mapping>.pk
      signing_key: <certificate>.pk
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the provider
  returned: always
  type: dict
  sample:
    access_token_validity: hours=1
    assigned_application_name: Grafana's dashboard
    assigned_application_slug: grafana-dashboard
    authorization_flow: <pk>
    component: ak-provider-oauth2-form
    name: benschubert-infrastructure-grafana
    pk: 1
"""


from typing import Any, NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def _compare(existing: dict[str, Any], final: dict[str, Any]) -> bool:
    if existing is not None:
        existing["property_mappings"] = sorted(existing["property_mappings"])
    if final is not None:
        final["property_mappings"] = sorted(final["property_mappings"])
    return existing == final


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["provider"] = {
        "type": "dict",
        "required": True,
        "options": {
            "name": {"type": "str", "required": True},
            "authorization_flow": {"type": "str", "required": True},
            "invalidation_flow": {"type": "str", "required": True},
            "redirect_uris": {
                "type": "list",
                "elements": "dict",
                "required": True,
            },
            "property_mappings": {
                "type": "list",
                "required": True,
                "elements": "str",
            },
            "signing_key": {"type": "str", "required": True},
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
        "/api/v3/providers/oauth2/",
        "pk",
        {"name": name},
        provider,
        state=module.params["state"],
        compare=_compare,
    )


if __name__ == "__main__":
    main()
