DOCUMENTATION = """
---
module: authentik_group

short_description: Allows administration of Authentik groups

description:
  - This module allows the administration of Authentik groups via the
    Authentik API.
  - See https://goauthentik.io/docs/user-group-role/groups

options:
  group:
    description:
      - The configuration for the specified group
    type: dict
    required: true
    suboptions:
      name:
        description:
          - The name of the group
          - Will be used to find the right group to create, delete or update.
        required: true
        type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Create a group named 'Grafana Admins'
  benschubert.infrastructure.authentik_group:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    group:
      name: Grafana Admins
"""

RETURN = """
data:
  description: The information returned by the Authentik API
  returned: always
  type: dict
  sample:
    name: Grafana Admins
    is_superuser: false
    pk: <pk>
    users:
      - 1
      - 2
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["group"] = {
        "type": "dict",
        "required": True,
        "options": {
            "name": {"type": "str", "required": True},
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    group = module.params["group"]

    execute(
        module,
        "/api/v3/core/groups/",
        "pk",
        {"name": group["name"]},
        group,
        state=module.params["state"],
    )


if __name__ == "__main__":
    main()
