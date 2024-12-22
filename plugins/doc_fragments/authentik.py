class ModuleDocFragment:
    DOCUMENTATION = """
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
  timeout:
    description:
      - The timeout to set when contacting the Authentik Server.
      - If your server is slow to respond, it might be necessary to bump this
    type: int
    default: 10
  validate_certs:
    description:
      - If false, SSL certificates will not be validated.
      - This should only set to false used on personally controlled sites
        using self-signed certificates.
    type: bool
    default: true
"""

    STATEFUL = """
options:
  state:
    description:
      - Whether the entity should exist or not
    type: str
    default: present
    choices:
      - present
      - absent
"""
