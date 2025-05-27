DOCUMENTATION = """
---
module: authentik_certificate_info

short_description: Allows retrieving information about certificates from the Authentik API

description:
  - This module allows retrieving information from certificates from the Authentik API
  - See https://docs.goauthentik.io/docs/sys-mgmt/certificates

options:
  name:
    description:
      - The name of the certificate to retrieve
    required: true
    type: str

extends_documentation_fragment:
  - benschubert.infrastructure.authentik

author:
  - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Retrieve the default certificate from Authentik
  benschubert.infrastructure.authentik_certificate_info]:
    authentik_token: <my-secret-token>
    authentik_url: https://authentik.test/
    name: authentik Self-signed Certificate
"""

RETURN = """
msg:
  description: Information on what happen
  returned: always
  type: str
  sample: Found certificate
data:
  description: The information returned by the Authentik API for the certificate
  returned: always
  type: dict
  sample:
    pk: 964f1e77-a608-48d4-afd1-3fa4db05d90a
    name: authentik Self-signed Certificate
    fingerprint_sha256: 46:62:a1:65:56:12:91:ef:c2:31:9d:79:36:9f:ad:9c:20:bc:c1:ea:8e:6b:67:b2:0f:32:53:48:82:ff:77:66
    fingerprint_sha1: fa:cc:39:b9:65:4f:0f:2f:8f:f6:34:d8:a0:3e:5d:ca:12:e0:05:b8
    cert_expiry: "2026-05-27T13:39:51Z"
    cert_subject: OU=Self-signed,O=authentik,CN=authentik Self-signed Certificate
    private_key_available: true
    private_key_type: rsa
    managed: null
"""


from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benschubert.infrastructure.plugins.module_utils.authentik import (
    Authentik,
    get_base_arguments,
)


def main() -> NoReturn:  # type: ignore[misc]
    argument_spec = get_base_arguments(include_state=False)
    argument_spec["name"] = {"type": "str", "required": True}

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    authentik = Authentik(module, "/api/v3/crypto/certificatekeypairs/")
    result = authentik.get_one({"name": module.params["name"]})
    module.exit_json(changed=False, data=result)


if __name__ == "__main__":
    main()
