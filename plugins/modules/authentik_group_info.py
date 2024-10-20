DOCUMENTATION = """
---
module: authentik_group_info

short_description: Allows retrieving information about groups from the Authentik API

description:
  - This module allows retrieving information from groups from the Authentik API
  - See https://docs.goauthentik.io/docs/users-sources/groups/

options:
  name:
    description:
      - The name of the group to get information for
    required: true
    type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Retrieve the authentik Admins group
  benschubert.infrastructure.authentik_group_info:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    name: authentik Admins
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the group
  returned: always
  type: dict
  sample:
    pk: <pk>
    name: authentik Admins
    parent: null
    users:
      - 1
      - 2
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = {
        **get_base_arguments(include_state=False),
        "name": {"type": "str", "required": True},
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    authentik = Authentik(module, "/api/v3/core/groups/")
    result = authentik.get_one({"name": module.params["name"]})
    module.exit_json(changed=False, data=result)


if __name__ == "__main__":
    main()
