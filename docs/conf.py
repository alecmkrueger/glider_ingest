# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'glider_ingest'
copyright = '2025, Alec Krueger'
author = 'Alec Krueger'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.napoleon',
    'autoapi.extension',
    'sphinx.ext.inheritance_diagram'
]

autoapi_dirs = ['../src']
autoapi_type = 'python'
autoapi_template_dir = '_templates'
autoapi_member_order = 'groupwise'
autoapi_options = [
    'members',
    'undoc-members',
    'show-inheritance',
    'show-module-summary',
]

# Suppress warnings for missing references and duplicates
suppress_warnings = ['autoapi', 'ref.python', 'autoapi.python_import_resolution']

templates_path = ['_templates']
exclude_patterns = []

autoapi_keep_files = True
autoapi_generate_api_docs = True

# Additional AutoAPI settings to handle duplicates and improve output
autoapi_python_class_content = 'class'
autoapi_add_toctree_entry = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True