DOCUMENTATION = """
---
module: authentik_propertymappings_scope_info

short_description: Allows retrieving information about OAuth2 scopes from the Authentik API

description:
  - This module allows retrieving information from OAuth2 scopes from the Authentik API
  - See https://goauthentik.io/docs/property-mappings/

options:
  scope_name:
    description:
      - The name of the scope to retrieve
    required: true
    type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Retrieve the profile scope
  benschubert.infrastructure.authentik_propertymappings_scope_info]:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    scope_name: profile
"""

RETURN = """
msg:
  description: Information on what happen
  returned: always
  type: str
  sample: entry is up to date
data:
  description: The information returned by the Authentik API for the scope
  returned: always
  type: dict
  sample:
    component: ak-property-mapping-scope-form
    description: General Profile Information
    expression: |-
      return {
          # Because authentik only saves the user's full name, and has no concept of first and last names,
          # the full name is used as given name.
          # You can override this behaviour in custom mappings, i.e. `request.user.name.split(" ")`
          "name": request.user.name,
          "given_name": request.user.name,
          "preferred_username": request.user.username,
          "nickname": request.user.username,
          # groups is not part of the official userinfo schema, but is a quasi-standard
          "groups": [group.name for group in request.user.ak_groups.all()],
      }
    managed: goauthentik.io/providers/oauth2/scope-profile
    meta_model_name: authentik_providers_oauth2.scopemapping
    name: 'authentik default OAuth Mapping: OpenID ''profile'''
    pk: a993d657-6480-4933-a6ff-e21215251660
    scope_name: profile
    verbose_name: Scope Mapping
    verbose_name_plural: Scope Mappings
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments(include_state=False)
    argument_spec["scope_name"] = {"type": "str", "required": True}

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    authentik = Authentik(module, "/api/v3/propertymappings/scope/")
    result = authentik.get_one({"scope_name": module.params["scope_name"]})
    module.exit_json(changed=False, data=result)


if __name__ == "__main__":
    main()
