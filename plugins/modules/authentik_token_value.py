DOCUMENTATION = """
---
module: authentik_token_value

short_description: Allows retrieving the value of the provided token

description:
  - This module allows retrieving a token by name from the Authentik API

options:
  token:
    description:
      - The name of the token for which to retrieve the value
    required: true
    type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Retrieve the token named test_token
  benschubert.infrastructure.authentik_token_value:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    token: test_token
"""

RETURN = """
key:
  description: The value of the token
  returned: always
  type: str
  sample: mytokenvalue
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
        "token": {"type": "str", "required": True},
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        no_log=True,
    )

    authentik = Authentik(module, "/api/v3/core/tokens/")
    result = authentik.request(f"{module.params['token']}/view_key/")
    module.exit_json(changed=False, key=result["key"])


if __name__ == "__main__":
    main()
