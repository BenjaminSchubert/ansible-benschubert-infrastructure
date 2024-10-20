DOCUMENTATION = """
---
module: authentik_outpost

short_description: Allows administration of Authentik outposts

description:
  - This module allows the administration of Authentik outposts via the
    Authentik API.
  - See https://docs.goauthentik.io/docs/add-secure-apps/outposts/
  - For connecting providers to outposts, please see
    benschubert.infrastructure.authentik_outpost_providers

options:
  outpost:
    description:
      - The configuration for the specified outpost
    type: dict
    required: true
    suboptions:
      name:
        description:
          - The name of the outpost to configure
        type: str
        required: true
      config:
        description:
          - The configuration for the outpost
        type: dict
        required: true
        suboptions:
          authentik_host:
            description:
              - The public URL at which the authentik service is available
            type: str
            required: true

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Set the builtin's embedded outpost host's URL
  benschubert.infrastructure.authentik_outpost:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    outpost:
      name: authentik Embedded Outpost
      config:
        authentik_host: https://authentik.test/
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the outpost
  returned: always
  type: dict
  sample:
    config:
      authentik_host: https://authentik.test
    name: authentik Embedded Outpost
    pk: <pk>
    providers:
      - 1
    providers_obj: <...>
    type: proxy
"""

from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["outpost"] = {
        "type": "dict",
        "required": True,
        "options": {
            "name": {"type": "str", "required": True},
            "config": {
                "type": "dict",
                "required": True,
                "options": {
                    "authentik_host": {"type": "str", "required": True},
                },
            },
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    outpost = module.params["outpost"]
    name = outpost["name"]

    execute(
        module,
        "/api/v3/outposts/instances/",
        "pk",
        {"name__iexact": name},
        outpost,
        state=module.params["state"],
    )


if __name__ == "__main__":
    main()
