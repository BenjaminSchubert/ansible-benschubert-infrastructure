DOCUMENTATION = """
---
module: github_content
short_description: Get the content of a file or directory on GitHub
description:
    - This module allows retrieving the metadata on content of a file or a
      directory of a project on GitHub through the GitHub API.
      Documentation on the API can be found at
      https://docs.github.com/en/rest/repos/contents
options:
    owner:
        description:
            - The owner of the repository
        required: true
        type: str
    path:
        description:
            - The path inside the repository for the file or directory
        required: true
        type: str
    ref:
        description:
            - The branch/tag/git id for which to get the path
        required: true
        type: str
    repo:
        description:
            - The repository name
        required: true
        type: str

author:
    - Benjamin Schubert (@benjaminschubert)
"""

EXAMPLES = """
- name: Get the license file info for the ansible repo
  github_content:
    owner: ansible
    path: COPYING
    ref: devel
    repo: ansible
  register: _ansible_license
"""

RETURN = """
msg:
  description: Information on what happen
  returned: always
  type: str
  sample: Retrieved file information
content:
    description: The information returned by the GitHub content API
    returned: always
    type: dict
    sample: See https://docs.github.com/en/rest/repos/contents
"""

import json
from http import HTTPStatus
from typing import NoReturn

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def main() -> NoReturn:  # type: ignore[misc]
    module = AnsibleModule(
        argument_spec={
            "owner": {"type": "str", "required": True},
            "repo": {"type": "str", "required": True},
            "path": {"type": "str", "required": True},
            "ref": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )

    p = module.params
    response, info = fetch_url(
        module,
        f"https://api.github.com/repos/{p['owner']}/{p['repo']}/contents/{p['path']}?ref={p['ref']}",
    )

    if info["status"] != HTTPStatus.OK:
        module.fail_json(
            msg=(
                f"Error contacting github at {info['url']}."
                " Received a {info['status']}:\n{response.read()}"
            )
        )

    result = json.loads(response.read())
    module.exit_json(
        changed=False, msg="Retrieved file information", content=result
    )


if __name__ == "__main__":
    main()
