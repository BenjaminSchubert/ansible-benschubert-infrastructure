# Ansible expects imports to be after the documentation
# Ansible modules are not on path by default
# pylint: disable=wrong-import-position,import-error

DOCUMENTATION = """
---
module: authentik_user_group

short_description: Allows adding or removing users to groups in Authentik

description:
  - This module allows the administration of Authentik group membership via the
    Authentik API.
  - See https://goauthentik.io/docs/user-group-role/user

options:
  group_pk:
    description:
      - The pk for the group to add or remove the user from
    type: str
    required: true
  user_pk:
    description:
      - The pk of the user to add or remove to the group
    type: str
    required: true

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Ensure the user with pk '123' is in the group '5'
  benschubert.infrastructure.user_group:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    group_pk: 5
    user_pk: 123
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the user
  returned: always
  type: dict
  sample:
    email: <user-email>
    groups:
      - <group1_pk>
      - <group2_pk>
    is_superuser: false
    pk: <user-pk>
    username: <user>
"""


import copy
from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["group_pk"] = {"type": "str", "required": True}
    argument_spec["user_pk"] = {"type": "str", "required": True}

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    group_pk = module.params["group_pk"]
    user_pk = module.params["user_pk"]

    authentik = Authentik(module, "/api/v3/core/users/")

    user = authentik.get(f"{user_pk}/")
    final_state = copy.deepcopy(user)

    if module.params["state"] == "absent":
        if group_pk not in user["groups"]:
            module.exit_json(changed=False, data=user)

        final_state["groups"].pop(group_pk)
        msg = "user removed from group"
    else:
        if group_pk in user["groups"]:
            module.exit_json(changed=False, data=user)

        final_state["groups"].append(group_pk)
        msg = "user added to group"

    if not module.check_mode:
        final_state = authentik.update(user_pk, final_state)

    module.exit_json(
        changed=True,
        diff={"before": user, "after": final_state},
        msg=msg,
        data=final_state,
    )


if __name__ == "__main__":
    main()
