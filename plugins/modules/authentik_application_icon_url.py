DOCUMENTATION = """
---
module: authentik_application_icon_url

short_description: Allows configuring application icons from the Authentik API

description:
  - This module allows configuring the icon urls for applications from the
    Authentik API
  - See https://docs.goauthentik.io/docs/applications#appearance

options:
  authentik_token:
    description:
      - The token used to authenticate against the Authentik server
    type: str
    required: true
  authentik_url:
    description:
      - The URL at which to contact the Authentik server
    type: str
    required: true
  ca_path:
    description:
      - PEM formatted file that contains a CA certificate to be used for
        validation
    type: str
  slug:
    description:
      - The slug identifying the application for which to configure the icon
    required: true
    type: str
  url:
    description:
      - The URL of the icon for the application
    required: true
    type: str
  validate_certs:
    description:
      - If false, SSL certificates will not be validated.
      - This should only set to false used on personally controlled sites
        using self-signed certificates.
    type: bool
    default: true

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Set the URL for the traefik application
  benschubert.infrastructure.authentik_application_icon_url:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    slug: traefik-dashboard
    url: https://traefik.test/dashboard/icons/favicon-32x32.png
"""

RETURN = """
data:
  description: The URL of the icon for the application
  returned: always
  type: str
  sample: https://traefik.test/dashboard/icons/favicon-32x32.png
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments()
    argument_spec.pop("state")
    argument_spec.update(
        {
            "slug": {"type": "str", "required": True},
            "url": {"type": "str", "required": True},
        },
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    slug = module.params["slug"]
    url = module.params["url"]

    authentik = Authentik(module, "/api/v3/core/applications/")

    current = authentik.get(slug)

    if current["meta_icon"] == url:
        module.exit_json(changed=False, data=current["meta_icon"])

    if not module.check_mode:
        authentik.request(
            f"{slug}/set_icon_url/",
            data={"url": url},
            method="POST",
        )

    module.exit_json(
        changed=True,
        diff={"before": current["meta_icon"], "after": url},
        msg="entry updated",
        data=url,
    )


if __name__ == "__main__":
    main()
