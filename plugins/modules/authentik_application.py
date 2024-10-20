DOCUMENTATION = """
---
module: authentik_application

short_description: Allows administration of Authentik applications

description:
  - This module allows the administration of Authentik applications via the
    Authentik API.
  - See https://docs.goauthentik.io/docs/applications

options:
  application:
    description:
      - The configuration for the specified application
    type: dict
    required: true
    suboptions:
      group:
        description:
          - The group in which to add the application on the Authentik UI
        type: str
      meta_description:
        description:
          - The description of the application
        type: str
      name:
        description:
          - The name of the application
        type: str
        required: true
      open_in_new_tab:
        description:
          - Whether the application should be opened in a new tab in the main
            application list
        type: bool
        default: false
      provider:
        description:
          - The id of the provider assigned to the application
        type: int
        required: true
      slug:
        description:
          - The slug used as a unique id for the application
        type: str
        required: true

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Configure an application for Traefik's dashboard
  benschubert.infrastructure.authentik_application:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    application:
      name: Traefik's dashboard
      slug: traefik-dashboard
      provider: 1
"""

RETURN = """
data:
  description: The information returned by the Authentik API
  returned: always
  type: dict
  sample:
    group: ""
    launch_url: https://traefik.test/
    name: Traefik's dashboard
    open_in_new_tab: false
    pk: <pk>
    provider: 1
    provider_obj: <...>
    slug: traefik-dashboard
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["application"] = {
        "type": "dict",
        "required": True,
        "options": {
            "name": {"type": "str", "required": True},
            "slug": {"type": "str", "required": True},
            "provider": {"type": "int", "required": True},
            "group": {"type": "str"},
            "meta_description": {"type": "str"},
            "open_in_new_tab": {"type": "bool", "default": False},
        },
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    application = module.params["application"]

    execute(
        module,
        "/api/v3/core/applications/",
        "slug",
        None,  # slug is always required we should not need this
        application,
        state=module.params["state"],
    )


if __name__ == "__main__":
    main()
