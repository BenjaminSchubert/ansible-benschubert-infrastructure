"""This module provides utilities to work with Authentik APIs."""

import json
from collections.abc import Callable
from http import HTTPStatus
from typing import Any, Literal, NoReturn, cast
from urllib.parse import urlencode, urljoin

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def get_base_arguments(include_state: bool = True) -> dict[str, Any]:
    """Get the base arguments required for the AUthentik utility."""
    base = {
        "authentik_url": {"type": "str", "required": True},
        "authentik_token": {"type": "str", "required": True, "no_log": True},
        "ca_path": {"type": "str", "required": False},
        "timeout": {"type": "int", "default": 10},
        "validate_certs": {"type": "bool", "default": True},
    }
    if include_state:
        base["state"] = {
            "type": "str",
            "choices": ["present", "absent"],
            "default": "present",
        }
    return base


class Authentik:
    """
    A utility to handle Authentik resources via APIs.

    :param module: the ansible module
    :param api_slug: The path to the resource type that is being handled
    """

    def __init__(self, module: AnsibleModule, api_slug: str) -> None:
        self._module = module
        self._url = module.params["authentik_url"]
        self._token = module.params["authentik_token"]
        self._ca_path = module.params["ca_path"]
        self._timeout = module.params["timeout"]
        self._api_slug = api_slug

    def request(  # type: ignore[return]  # noqa: RET503
        self,
        endpoint: str = "",
        data: dict[str, Any] | None = None,
        queryparams: dict[str, str] | None = None,
        method: Literal["DELETE", "GET", "POST", "PUT"] = "GET",
    ) -> dict[str, Any] | None:
        """
        Execute the provided request on the server.

        :param endpoint: The endpoint on the authentik server.
                         This will be prependedbu the url and api_slug
        :param data; The data to add to the request
        :param queryparams: The parameters to add as url query parameters
        :param method: The http method to use
        :return: The data returned by the server
        """
        url = urljoin(self._url, self._api_slug)
        if endpoint:
            url = urljoin(url, endpoint)

        if queryparams is not None:
            params = urlencode(queryparams)
            url += f"?{params}"

        response, info = fetch_url(
            self._module,
            url,
            data=json.dumps(data) if data else None,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            ca_path=self._ca_path,
            method=method,
            timeout=self._timeout,
        )

        if info["status"] == HTTPStatus.NO_CONTENT:
            return None
        if info["status"] in [HTTPStatus.OK, HTTPStatus.CREATED]:
            return cast("dict[str, Any]", json.loads(response.read()))
        if info["status"] == HTTPStatus.NOT_FOUND:
            return None

        self._module.fail_json(
            msg=f"Error contacting Authentik at {info['url']},"
            f" received a {info['status']}:"
            f" {info.get('body', info.get('msg'))}",
        )

    def get_one(  # type: ignore[return]  # noqa: RET503
        self,
        queryparams: dict[str, str],
    ) -> dict[str, Any] | None:
        """
        Search and return one resource with the provided query parameters.

        If multiple resources are matched, this will error.

        :param queryparams: A search query to identify a unique resource
        :return: The resource
        """
        result = self.request(queryparams=queryparams)
        assert result is not None

        results = result["results"]
        if len(results) == 0:
            return None
        if len(results) == 1:
            return cast("dict[str, Any]", results[0])

        self._module.fail_json(
            msg="Expected only one result back from api",
            result=results,
        )

    def get(self, identifier: str) -> dict[str, Any] | None:
        """
        Get the value of the resource identify by the provided identifier.

        :param identifier: The identifier for the resource to get
        :return: The value of the data on the service
        """
        return self.request(f"{identifier}/")

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new resource with the provided data.

        :param data: The value of the resource to create
        :return: The value of the data on the service
        """
        result = self.request(data=data, method="POST")
        assert result is not None
        return result

    def delete(self, identifier: str) -> dict[str, Any] | None:
        """
        Delete the resource with the specified identifier.

        :param identifier: where the resource lives
        :return: The deleted value, None if it did not exist
        """
        return self.request(f"{identifier}/", method="DELETE")

    def update(self, identifier: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Update the resource with the specified identifier.

        :param identifier: where the resource lives
        :param data: the value of the resource
        :return: The full value of the updated data
        """
        result = self.request(f"{identifier}/", data=data, method="PUT")
        assert result is not None
        return result


def _compare(
    existing: dict[str, Any] | None, final: dict[str, Any] | None
) -> bool:
    return existing == final


def execute(  # type: ignore[misc]
    module: AnsibleModule,
    api_slug: str,
    pk_name: str,
    search_query: dict[str, str] | None,
    desired_value: dict[str, Any],
    state: Literal["absent", "present"],
    compare: Callable[
        [dict[str, Any] | None, dict[str, Any] | None], bool
    ] = _compare,
    find: Callable[[Authentik], dict[str, Any] | None] | None = None,
) -> NoReturn:
    """
    Ensure the selected Authentik resource is in the desired state.

    :param module: The ansible module
    :param api_slug: The api path for the resource
    :param pk_name: The name of the unique id when resource can be uniquely
                    identified by one
    :param search_query: The query used to search for the selected entry if the
                         primary key is not otherwise known
    :param desired_value: The wanted value
    :param state: The state in which we want the value. Absent will delete it
                  if it exists. If 'present', this acts as a PATCH query, and
                  updates the current value without modifying non-specified
                  fields.
    :param find: If there is no API to find the exact value, this can be a
                 callable that returns the value while talking to the API.
    """
    authentik = Authentik(module, api_slug)

    if pk := desired_value.get(pk_name):
        existing_value = authentik.get(pk)
    elif find is not None:
        existing_value = find(authentik)
    elif search_query is not None:
        existing_value = authentik.get_one(search_query)
    else:
        module.fail_json(
            msg="No search query provided, no custom find method and no primary key.",
        )

    if state == "absent":
        if existing_value is None:  # pylint: disable=possibly-used-before-assignment
            module.exit_json(
                changed=False,
                msg="entry is already absent",
                data=None,
            )

        # mypy is not smart enough to understand the above exit_json
        # doesn't return
        assert existing_value is not None

        if not module.check_mode:
            authentik.delete(existing_value[pk_name])

        module.exit_json(
            changed=True,
            diff={"before": existing_value, "after": None},
            msg="entry deleted.",
            data=None,
        )

    if existing_value is None:
        final_value = desired_value
    else:
        final_value = existing_value | desired_value

    if compare(existing_value, final_value):
        module.exit_json(
            changed=False,
            msg="entry is up to date",
            data=final_value,
        )

    if not module.check_mode:
        if existing_value is None:
            final_value = authentik.create(final_value)
        else:
            final_value = authentik.update(final_value[pk_name], final_value)

    module.exit_json(
        changed=True,
        diff={"before": existing_value, "after": final_value},
        msg="entry updated",
        data=final_value,
    )
