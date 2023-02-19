DOCUMENTATION = """
---
module: authentik_flow_info

short_description: Allows retrieving information about flows from the Authentik API

description:
  - This module allows retrieving information from flows from the Authentik API
  - See https://goauthentik.io/docs/flow

options:
  slug:
    description:
      - The slug identifying the authentik flow
    required: true
    type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Retrieve the authentik flow
  benschubert.infrastructure.authentik_flow_info:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    slug: default-provider-authorization-explicit-consent
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the flow
  returned: always
  type: dict
  sample:
    authentication: require_authenticated
    denied_action: message_continue
    designation: authorization
    layout: stacked
    name: Authorize Application
    pk: <pk>
    slug: default-provider-authorization-explicit-consent
    stages: <...>
    title: Redirecting to %(app)s
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["slug"] = {"type": "str", "required": True}

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    authentik = Authentik(module, "/api/v3/flows/instances/")
    result = authentik.get_one({"slug": module.params["slug"]})
    module.exit_json(changed=False, data=result)


if __name__ == "__main__":
    main()
