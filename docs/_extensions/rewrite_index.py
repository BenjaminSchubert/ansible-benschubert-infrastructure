from typing import Any

from docutils import nodes
from docutils.transforms import Transform
from sphinx import addnodes
from sphinx.application import Sphinx


class RewriteIndex(Transform):
    default_priority = 500

    def apply(self, **kwargs: Any) -> None:  # noqa: ARG002
        if self.document.settings.env.docname != "index":
            return

        self._reformat_toctree()
        self._rename_references()
        self._switch_plugin_and_roles_sections()

    def _switch_plugin_and_roles_sections(self) -> None:
        plugins_index = None
        roles_index = None
        for section in self.document.findall(nodes.section):
            if section["ids"] == ["plugin-index"]:
                plugins_index = section
            elif section["ids"] == ["role-index"]:
                roles_index = section

        assert plugins_index is not None
        assert roles_index is not None

        plugins_index.replace_self(roles_index.deepcopy())
        roles_index.replace_self(plugins_index.deepcopy())

    def _reformat_toctree(self) -> None:
        def rename(target: str) -> str:
            if target.endswith("_module"):
                return target[:-7]
            if target.endswith("_role"):
                return target[:-5]
            return target

        for section in self.document.findall(addnodes.toctree):
            section["entries"] = [
                (rename(target) if title is None else title, target)
                for title, target in section["entries"]
            ]

        for section in self.document.findall(nodes.section):
            if section["ids"] == ["role-index"]:
                caption = "Roles"
            elif section["ids"] == ["modules"]:
                caption = "Modules"
            else:
                continue

            toctree = list(section.findall(addnodes.toctree))
            assert len(toctree) == 1
            toctree[0]["rawcaption"] = caption
            toctree[0]["caption"] = caption

    def _rename_references(self) -> None:
        for section in self.document.findall(nodes.section):
            if section["ids"] == ["role-index"]:
                extra = " role"
            elif section["ids"] == ["modules"]:
                extra = " module"
            else:
                continue

            for entry in section.findall(nodes.inline):
                entry.replace(
                    entry.children[0],
                    nodes.Text(
                        f"benschubert.infrastructure.{entry.children[0].removesuffix(extra)}",
                    ),
                )


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_transform(RewriteIndex)
    return {"parallel_read_safe": True}
