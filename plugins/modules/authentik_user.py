DOCUMENTATION = """
---
module: authentik_user

short_description: Allows administration of Authentik users

description:
  - This module allows the administration of Authentik users via the
    Authentik API.
  - See https://docs.goauthentik.io/docs/users-sources/user/

options:
  user:
    description:
      - The configuration for the specified user
    type: dict
    required: true
    suboptions:
      name:
        description:
          - The "display" name of the user
        required: true
        type: str
      path:
        description:
          - The path under which to keep the user in Authentik, for organization
            purpose
        default: users
        type: str
      username:
        description:
          - The username of the user, used to login, and find the user.
        required: true
        type: str
      type:
        description:
          - The type of user that is created
        default: internal
        choices: [internal, service_account]
        type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Create a user named 'testuser'
  benschubert.infrastructure.authentik_user:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    user:
      name: Test User
      username: testuser
"""

RETURN = """
data:
  description: The information returned by the Authentik API
  returned: always
  type: dict
  sample:
    name: Test User
    username: testuser
    type: internal
    is_superuser: false
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["user"] = {
        "type": "dict",
        "required": True,
        "options": {
            "name": {"type": "str", "required": True},
            "path": {"type": "str", "default": "users"},
            "username": {"type": "str", "required": True},
            "type": {
                "type": "str",
                "choices": ["internal", "service_account"],
                "default": "internal",
            },
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    user = module.params["user"]

    execute(
        module,
        "/api/v3/core/users/",
        "pk",
        {"username": user["username"]},
        user,
        state=module.params["state"],
    )


if __name__ == "__main__":
    main()
