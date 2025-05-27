DOCUMENTATION = """
---
module: authentik_propertymappings_scope

short_description: Allows administration of Authentik scope propertymappings

description:
  - This module allows the administration of Authentik scope propertymappings
    via the Authentik API.
  - See https://docs.goauthentik.io/docs/add-secure-apps/providers/property-mappings/

options:
  scope:
    description:
      - The configuration for the specified group
    type: dict
    required: true
    suboptions:
        description:
          description:
            - Describe what this scope is for
          required: true
          type: str
        expression:
          description:
            - The actual implementation
          required: true
          type: str
        name:
          description:
            - The name of the scope as shown in Authentik
          required: true
          type: str
        scope_name:
          description:
            - The name of the scope as claimed by the client
          required: true
          type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Create a scope named 'nextcloud_quota'
  benschubert.infrastructure.authentik_propertymappings_scope:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    scope:
      name: Nextcloud quota
      scope_name: nextcloud_quota
      description: Scope representing available quota for Nextcloud usage
      expression: "return {'quota': user.group_attributes().get('nextcloud_quota', '10 GB')}"
"""

RETURN = """
data:
  description: The information returned by the Authentik API
  returned: always
  type: dict
  sample:
    name: Nextcloud quota
    scope_name: nextcloud_quota
    description: Scope representing available quota for Nextcloud usage
    expression: "return {'quota': user.group_attributes().get('nextcloud_quota', '10 GB')}"
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["scope"] = {
        "type": "dict",
        "required": True,
        "options": {
            "description": {"type": "str", "required": True},
            "expression": {"type": "str", "required": True},
            "name": {"type": "str", "required": True},
            "scope_name": {"type": "str", "required": True},
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    scope = module.params["scope"]

    execute(
        module,
        "/api/v3//propertymappings/provider/scope/",
        "pk",
        {"name": scope["name"]},
        scope,
        state=module.params["state"],
    )


if __name__ == "__main__":
    main()
