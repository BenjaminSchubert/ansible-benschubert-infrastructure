import sys
from pathlib import Path

DOCS_PATH = Path(__file__).parent
EXTENSIONS_PATH = DOCS_PATH / "_extensions"

sys.path.append(str(EXTENSIONS_PATH))

project = "benschubert.infrastructure"
copyright = "Benjamin Schubert"  # noqa: A001

title = "benschubert.infrastructure"
html_short_title = "benschubert.infrastructure"

nitpicky = True

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_antsibull_ext",
    "sphinxcontrib.spelling",
    # Internal extensions
    "rewrite_index",
]

pygments_style = "ansible"
highlight_language = "YAML+Jinja"
html_theme = "sphinx_ansible_theme"
html_show_sphinx = False
display_version = False
html_use_smartypants = True
html_use_modindex = False
html_use_index = False
html_copy_source = False

html_theme_options = {
    "vcs_pageview_mode": "edit",
    "topbar_links": {},
}

intersphinx_mapping = {
    "python3": ("https://docs.python.org/3/", None),
    "jinja2": ("http://jinja.palletsprojects.com/", None),
    "ansible_devel": ("https://docs.ansible.com/ansible/devel/", None),
}

# Linkcheck config
linkcheck_ignore = ["https://docs.goauthentik.io/docs/applications"]

# Spelling config
spelling_show_suggestions = True
spelling_word_list_filename = str(DOCS_PATH / "_spelling_allowlist.txt")
