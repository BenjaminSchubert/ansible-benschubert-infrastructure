from typing import Any, cast

from docutils import nodes
from docutils.transforms import Transform
from sphinx import addnodes
from sphinx.application import Sphinx


class RewriteIndex(Transform):
    default_priority = 500

    def apply(self, **kwargs: Any) -> None:  # noqa: ARG002
        if self.document.settings.env.docname != "index":
            return

        self._remove_version()
        self._prettify_description()
        self._reformat_toctree()
        self._rename_references()
        self._switch_plugin_and_roles_sections()

    def _remove_version(self) -> None:
        node = self.document.next_node(nodes.section)
        assert "benschubert-infrastructure" in node["ids"]
        versions = node.next_node(nodes.paragraph)
        assert str(versions.children[0]) == "Collection version 0.0.1"
        node.remove(versions)

    def _prettify_description(self) -> None:
        # FIXME: if we could get antsibull to actually support rich descriptions
        #        it would allow us to remove all this
        description_section = None
        for section in self.document.findall(nodes.section):
            if section["ids"] == ["description"]:
                description_section = section
                break

        # Validate the format
        assert description_section is not None
        assert (
            str(description_section.children[0].children[0]) == "Description"
        )
        old_description = cast(
            "nodes.Element", description_section.children[1]
        )
        new_description = []

        paragraph = nodes.paragraph()
        for child in cast("list[nodes.Node]", old_description):
            if isinstance(child, nodes.Text) and "\x00<br /\x00>" in child:
                lines = child.split("\x00<br /\x00>")
                for entry in lines[:-1]:
                    paragraph.append(nodes.Text(entry))
                    new_description.append(paragraph)
                    paragraph = nodes.paragraph()

                paragraph.append(nodes.Text(lines[-1]))
                continue

            paragraph.append(child)

        new_description.append(paragraph)

        old_description.replace_self(new_description)
        for paragraph in new_description:
            self._unescape_list(paragraph)

    def _unescape_list(self, paragraph: nodes.paragraph) -> None:
        first_child = paragraph.children[0]
        list_indicator = "\n\x00* \x00"
        if not (
            isinstance(first_child, nodes.Text)
            and first_child.startswith(list_indicator)
        ):
            return

        list_elements = nodes.bullet_list()
        current_item = nodes.paragraph()

        for child in paragraph.children:
            if isinstance(child, nodes.Text) and list_indicator in child:
                items = child.split(list_indicator)
                for item in items[:-1]:
                    current_item.append(nodes.Text(item))
                    list_elements.append(nodes.list_item("", current_item))
                    current_item = nodes.paragraph()

                current_item.append(nodes.Text(items[-1]))
                continue

            current_item.append(child)
        list_elements.append(nodes.list_item("", current_item))

        paragraph.replace_self(list_elements)

    def _switch_plugin_and_roles_sections(self) -> None:
        plugins_index = None
        roles_index = None
        for section in self.document.findall(nodes.section):
            if "plugin-index" in section["ids"]:
                plugins_index = section
            elif "role-index" in section["ids"]:
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

        for toctree in self.document.findall(addnodes.toctree):
            toctree["entries"] = [
                (rename(target) if title is None else title, target)
                for title, target in toctree["entries"]
            ]

        for section in self.document.findall(nodes.section):
            if section["ids"] == ["role-index"]:
                caption = "Roles"
            elif section["ids"] == ["modules"]:
                caption = "Modules"
            else:
                continue

            toctrees = list(section.findall(addnodes.toctree))
            assert len(toctrees) == 1
            toctrees[0]["rawcaption"] = caption
            toctrees[0]["caption"] = caption

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
                        f"benschubert.infrastructure.{cast('str', entry.children[0]).removesuffix(extra)}",
                    ),
                )


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_transform(RewriteIndex)
    return {"parallel_read_safe": True}
