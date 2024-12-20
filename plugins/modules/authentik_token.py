DOCUMENTATION = """
---
module: authentik_token

short_description: Allows administration of Authentik tokens

description:
  - This module allows the administration of Authentik tokens via the
    Authentik API.
  - See https://docs.goauthentik.io/docs/add-secure-apps/providers/oauth2/client_credentials

options:
  token:
    description:
      - The configuration for the specified token
    type: dict
    required: true
    suboptions:
      identifier:
        description:
          - The unique identifier for the token
        required: true
        type: str
      intent:
        description:
          - "The intended usage for the token:"
          - "C(app_password): for authenticating against other applications"
          - "C(api): for authenticating with the Authentik API"
        type: str
        choices: [app_password, api]
        required: true
      user:
        description:
          - The primary key of the user owning the token
        required: true
        type: int
      description:
        description:
          - A description to attach to the token
        type: str
      expiring:
        description:
          - Whether the token expires or not
        type: bool
        default: true

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Create a token for user 2
  benschubert.infrastructure.authentik_token:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    token:
      identifier: my-test-token
      intent: app_password
      user: 2
      description: A token used during tests
      expiring: false
"""

RETURN = """
data:
  description: The information returned by the Authentik API
  returned: always
  type: dict
  sample:
    description: A token used during tests
    expiring: false
    identifier: my-test-token
    user: 6
    intent: app_password
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["token"] = {
        "type": "dict",
        "required": True,
        "options": {
            "identifier": {"type": "str", "required": True},
            "intent": {
                "type": "str",
                "choices": ["app_password", "api"],
                "required": True,
            },
            "user": {"type": "int", "required": True},
            "description": {"type": "str", "required": False},
            "expiring": {"type": "bool", "default": True},
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    token = module.params["token"]

    execute(
        module,
        "/api/v3/core/tokens/",
        "identifier",
        None,
        token,
        state=module.params["state"],
    )


if __name__ == "__main__":
    main()
