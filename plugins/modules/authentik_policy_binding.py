DOCUMENTATION = """
module: authentik_policy_binding

short_description: Allow administration of policy bindings in Authentik

description:
  - This module allows the administration of Policy bindings  via the Authentik
    API
  - See https://docs.goauthentik.io/docs/customize/policies/working_with_policies/

options:
  binding:
    description:
      - The configuration for the binding
      - At least one of C(group), C(policy) or C(user) needs to be provided
    type: dict
    required: true
    suboptions:
      enabled:
        description:
          - Whether the policy is enabled or not
        type: bool
        default: true
      failure_result:
        description:
          - The result if the policy execution fails
        type: bool
        default: false
      group:
        description:
          - The pk of the group to allow/deny access to the given flow or application
        type: str
        default: null
      negate:
        description:
          - Negates the outcome of the policy
        type: bool
        default: false
      order:
        description:
          - The place in the list of policies bindings where this needs to be
            evaluated
        type: int
        required: true
      policy:
        description:
          - The policy to bind against the target
        type: str
        default: null
      target:
        description:
          - The pk of the flow or application against which the policy must be
            bound
        type: str
        required: true
      user:
        description:
          - The pk of the user to allow/deny access to the given flow or application
        type: str
        default: null

extends_documentation_fragment:
  - benschubert.infrastructure.authentik
  - benschubert.infrastructure.authentik.stateful

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Restrict access to app {{ app }} to group {{ group }}
  benschubert.infrastructure.policy_binding:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test
    binding:
      group: "{{ group.pk }}"
      order: 0
      target: "{{ app.pk }}"

- name: Forbid access to app {{ app }} from user {{ user }}
  benschubert.infrastructure.policy_binding:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test
    binding:
      negate: true
      order: 0
      user: "{{ user.pk }}"
      target: "{{ app.pk }}"

- name: Bind the policy {{ policy }} to the flow {{ flow }}
  benschubert.infrastructure.policy_binding:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test
    binding:
      order: 0
      policy: "{{ policy.pk }}"
      target: "{{ flow.pk }}"
"""


from typing import Any, NoReturn, cast

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    execute,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec["binding"] = {
        "type": "dict",
        "required": True,
        "options": {
            "enabled": {"type": "bool", "default": True},
            "failure_result": {"type": "bool", "default": False},
            "group": {"type": "str"},
            "negate": {"type": "bool", "default": False},
            "order": {"type": "int", "required": True},
            "policy": {"type": "str"},
            "target": {"type": "str", "required": True},
            "user": {"type": "str"},
        },
        "required_one_of": [("group", "policy", "user")],
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    binding = module.params["binding"]

    # The Authentik API doesn't allow search by group or user
    def find(authentik: Authentik) -> dict[str, Any] | None:
        if binding["policy"] is not None:
            return cast(
                "dict[str, Any] | None",
                authentik.get_one(
                    {"target": binding["target"], "policy": binding["policy"]}
                ),
            )

        resp = authentik.request(queryparams={"target": binding["target"]})
        assert resp is not None

        for result in resp["results"]:
            for key in ["group", "user"]:
                if binding[key] is not None and binding[key] == result[key]:
                    return cast("dict[str, Any] | None", result)

        return None

    execute(
        module,
        "/api/v3/policies/bindings/",
        pk_name="pk",
        search_query=None,
        desired_value=binding,
        state=module.params["state"],
        find=find,
    )


if __name__ == "__main__":
    main()
