# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'Odata'
copyright = '2023, lukaqueres'
author = 'Lukaqueres'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

rst_prolog = """

.. meta::
    :title: Welcome to odata documentation
    :description: Odata python library documentation
    :keywords: python, library, odata, documentation, api, creodias, codede

"""

html_static_path = ['_static']

html_css_files = ['custom.css',
                  ('custom.css', {'media': 'print'})]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
