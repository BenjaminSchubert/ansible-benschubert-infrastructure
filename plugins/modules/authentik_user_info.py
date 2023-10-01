# Ansible expects imports to be after the documentation
# Ansible modules are not on path by default
# pylint: disable=wrong-import-position,import-error

DOCUMENTATION = """
---
module: authentik_user_info

short_description: Allows retrieving information about users from the Authentik API

description:
  - This module allows retrieving information from users from the Authentik API
  - See https://goauthentik.io/docs/user-group-role/user

options:
  username:
    description:
      - The name of the user to get information for
    required: true
    type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Retrieve the akadmin user
  benschubert.infrastructure.authentik_user_info:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    username: akadmin
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the user
  returned: always
  type: dict
  sample:
    pk: <pk>
    name: akadmin
    is_superuser: true
    uid: <uid>
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
        "username": {"type": "str", "required": True},
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    authentik = Authentik(module, "/api/v3/core/users/")
    result = authentik.get_one({"username": module.params["username"]})
    module.exit_json(changed=False, data=result)


if __name__ == "__main__":
    main()
