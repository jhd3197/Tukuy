import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Tukuy'
copyright = '2024, Tukuy'
author = 'Tukuy'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
napoleon_include_init_with_doc = True