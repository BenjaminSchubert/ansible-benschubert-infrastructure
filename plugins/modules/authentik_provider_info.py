# Ansible expects imports to be after the documentation
# Ansible modules are not on path by default
# pylint: disable=wrong-import-position,import-error

DOCUMENTATION = """
---
module: authentik_provider_info

short_description: Allows retrieving information about providers from the Authentik API

description:
  - This module allows retrieving information from providers from the Authentik API
  - See https://goauthentik.io/docs/providers/oauth2

options:
  name:
    description:
      - The name of the provider to get information for
    required: true
    type: str
  type:
    description:
      - The type of provider that is expected
    required: true
    type: str
    choices:
      - oauth2

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Retrieve the oauth2 provider for grafana
  benschubert.infrastructure.authentik_flow_info:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    name: grafana
    type: oauth2
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the provider
  returned: always
  type: dict
  sample:
    pk: <pk>
    name: grafana
    client_id: <client id>
    client_secret: <client secret>
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = {
        **get_base_arguments(),
        "name": {"type": "str", "required": True},
        "type": {"type": "str", "required": True, "choices": ["oauth2"]},
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    authentik = Authentik(
        module, f"/api/v3/providers/{module.params['type']}/"
    )
    result = authentik.get_one({"name": module.params["name"]})
    module.exit_json(changed=False, data=result)


if __name__ == "__main__":
    main()
