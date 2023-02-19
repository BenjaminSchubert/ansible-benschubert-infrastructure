DOCUMENTATION = """
---
module: authentik_outpost_provider

short_description: Allows connecting Authentik providers to outposts

description:
  - This module allows the administration of Authentik outposts connections with
    providers via the Authentik API.
  - See https://goauthentik.io/docs/outposts/

options:
  provider_pk:
    description:
      - The private key of the provider to configure
    required: true
    type: int
  outpost_name:
    description:
      - The name of the outpost that should handle the given provider
    required: true
    type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Configure the traefik provider to use the builtin outpost
  benschubert.infrastructure.authentik_outpost_provider:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    outpost_name: authentik Embedded Outpost
    provider_pk: <pk>
"""

RETURN = """
data:
  description: The information returned by the Authentik API for the outpost
  returned: always
  type: dict
  sample:
    config:
      authentik_host: https://authentik.test
    name: authentik Embedded Outpost
    pk: <pk>
    providers:
      - 1
    providers_obj: <...>
    type: proxy
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
    argument_spec.update(
        {
            "outpost_name": {"type": "str", "required": True},
            "provider_pk": {"type": "int", "required": True},
        },
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    outpost_name = module.params["outpost_name"]
    provider_pk = module.params["provider_pk"]

    authentik = Authentik(module, "/api/v3/outposts/instances/")

    outpost = authentik.get_one({"name__iexact": outpost_name})
    final_state = copy.deepcopy(outpost)

    if module.params["state"] == "absent":
        if provider_pk not in outpost["providers"]:
            module.exit_json(changed=False, data=outpost)

        final_state["providers"].pop(provider_pk)
        msg = "provider removed"
    else:
        if provider_pk in outpost["providers"]:
            module.exit_json(changed=False, data=outpost)

        final_state["providers"].append(provider_pk)
        msg = "provider added"

    if not module.check_mode:
        final_state = authentik.update(outpost["pk"], final_state)

    module.exit_json(
        changed=True,
        diff={"before": outpost, "after": final_state},
        msg=msg,
        data=final_state,
    )


if __name__ == "__main__":
    main()
