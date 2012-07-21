# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------
# Copyright (c) 2009  Jendrik Seipp
#
# RedNotebook is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RedNotebook is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with RedNotebook; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# -----------------------------------------------------------------------

import logging
import os
import re
import sys

import gobject
import pango

# Testing
if __name__ == '__main__':
    sys.path.insert(0, '../../')
    logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s %(message)s',)

from rednotebook.external import txt2tags


# Linebreaks are only allowed at line ends
REGEX_LINEBREAK = r'\\\\[\s]*$'
REGEX_HTML_LINK = r'<a.*?>(.*?)</a>'

TABLE_HEAD_BG = '#aaa'

CHARSET_UTF8 = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'

CSS = """\
<style type="text/css">
    body {
        font-family: Ubuntu, Helvetica, Arial, sans-serif;
    }
    blockquote {
        margin: 1em 2em;
        border-left: 2px solid #999;
        font-style: oblique;
        padding-left: 1em;
    }
    blockquote:first-letter {
        margin: .2em .1em .1em 0;
        font-size: 160%%;
        font-weight: bold;
    }
    blockquote:first-line {
        font-weight: bold;
    }
    table {
        border-collapse: collapse;
    }
    td, th {
        <!--border: 1px solid #888;--> <!--Allow tables without borders-->
        padding: 3px 7px 2px 7px;
    }
    th {
        text-align: left;
        padding-top: 5px;
        padding-bottom: 4px;
        background-color: %(TABLE_HEAD_BG)s;
        color: #ffffff;
    }
    hr.heavy {
        height: 2px;
        background-color: black;
    }
</style>
""" % globals()

# MathJax
FORMULAS_SUPPORTED = True
MATHJAX_FILE = 'http://cdn.mathjax.org/mathjax/latest/MathJax.js'
logging.info('MathJax location: %s' % MATHJAX_FILE)
MATHJAX_FINISHED = 'MathJax finished'

MATHJAX = """\
<script type="text/x-mathjax-config">
  MathJax.Hub.Config({
  messageStyle: "none",
  config: ["MMLorHTML.js"],
  jax: ["input/TeX","input/MathML","output/HTML-CSS","output/NativeMML"],
  tex2jax: {
      inlineMath: [ ['$','$'] ],
      displayMath: [ ['$$','$$'] ],
      processEscapes: true
    },
  extensions: ["tex2jax.js","mml2jax.js","MathMenu.js","MathZoom.js"],
  TeX: {
    extensions: ["AMSmath.js","AMSsymbols.js","noErrors.js","noUndefined.js"]
  }
  });
</script>
<script type="text/javascript"
  src="%s">
</script>
<script>
  MathJax.Hub.Queue(function () {
    document.title = "%s";
    document.title = "RedNotebook";
  });
</script>
""" % (MATHJAX_FILE, MATHJAX_FINISHED)


def convert_categories_to_markup(categories, with_category_title=True):
    # Only add Category title if the text is displayed
    if with_category_title:
        markup = '== %s ==\n' % _('Tags')
    else:
        markup = ''

    for category, entry_list in categories.iteritems():
        markup += '- ' + category + '\n'
        for entry in entry_list:
            markup += '  - ' + entry + '\n'
    markup += '\n\n'
    return markup


def get_markup_for_day(day, with_text=True, categories=None, date=None):
    '''
    Used for exporting days
    '''
    export_string = ''

    # Add date if it is not None and not the empty string
    if date:
        export_string += '= %s =\n\n' % date

    # Add text
    if with_text:
        export_string += day.text

    # Add Categories
    category_content_pairs = day.get_category_content_pairs()

    if categories:
        categories = [word.lower() for word in categories]
        export_categories = dict((x,y) for (x, y) in category_content_pairs.items()
                                 if x.lower() in categories)
    elif categories is None:
        # No restrictions
        export_categories = category_content_pairs
    else:
        # "Export no categories" selected
        export_categories = []


    if export_categories:
        export_string += '\n\n\n' + convert_categories_to_markup(export_categories,
                                                            with_category_title=with_text)
    elif with_text:
        export_string += '\n\n'

    # Only return the string, when there is text or there are categories
    # We don't want to list empty dates
    if export_categories or with_text:
        export_string += '\n\n\n'
        return export_string

    return ''


def _get_config(type):

    config = {}

    # Set the configuration on the 'config' dict.
    config = txt2tags.ConfigMaster()._get_defaults()

    # The Pre (and Post) processing config is a list of lists:
    # [ [this, that], [foo, bar], [patt, replace] ]
    config['postproc'] = []
    config['preproc'] = []

    # Allow line breaks, r'\\\\' are 2 \ for regexes
    config['preproc'].append([REGEX_LINEBREAK, 'LINEBREAK'])

    if type == 'xhtml' or type == 'html':
        config['encoding'] = 'UTF-8'  # document encoding
        config['toc'] = 0
        config['css-sugar'] = 1

        # Fix encoding for export opened in firefox
        config['postproc'].append([r'<head>', '<head>' + CHARSET_UTF8])

        # Custom css
        config['postproc'].append([r'</head>', CSS + '</head>'])

        # Line breaks
        config['postproc'].append([r'LINEBREAK', '<br />'])

        # Apply image resizing
        config['postproc'].append([r'src=\"WIDTH(\d+)-', r'width="\1" src="'])

    elif type == 'tex':
        config['encoding'] = 'utf8'
        config['preproc'].append(['€', 'Euro'])

        # Latex only allows whitespace and underscores in filenames if
        # the filename is surrounded by "...". This is in turn only possible
        # if the extension is omitted
        config['preproc'].append([r'\[""', r'["""'])
        config['preproc'].append([r'""\.', r'""".'])

        scheme = 'file:///' if sys.platform == 'win32' else 'file://'

        # For images we have to omit the file:// prefix
        config['postproc'].append([r'includegraphics\{(.*)"%s' % scheme, r'includegraphics{"\1'])
        #config['postproc'].append([r'includegraphics\{"file://', r'includegraphics{"'])

        # Special handling for LOCAL file links (Omit scheme, add run:)
        # \htmladdnormallink{file.txt}{file:///home/user/file.txt}
        # -->
        # \htmladdnormallink{file.txt}{run:/home/user/file.txt}
        config['postproc'].append([r'htmladdnormallink\{(.*)\}\{%s(.*)\}' % scheme,
                                   r'htmladdnormallink{\1}{run:\2}'])

        # Line breaks
        config['postproc'].append([r'LINEBREAK', r'\\\\'])

        # Apply image resizing
        config['postproc'].append([r'includegraphics\{("?)WIDTH(\d+)-', r'includegraphics[width=\2px]{\1'])

        # We want the plain latex formulas unescaped
        config['preproc'].append([r'\$\$\s*(.+?)\s*\$\$', r"BEGINEQUATION''\1''ENDEQUATION"])
        config['postproc'].append([r'BEGINEQUATION(.+)ENDEQUATION', r'$$\1$$'])
        config['preproc'].append([r'\$\s*(.+?)\s*\$', r"BEGINMATH''\1''ENDMATH"])
        config['postproc'].append([r'BEGINMATH(.+)ENDMATH', r'$\1$'])

    elif type == 'txt':
        # Line breaks
        config['postproc'].append([r'LINEBREAK', '\n'])

        # Apply image resizing ([WIDTH400-file:///pathtoimage.jpg])
        config['postproc'].append([r'\[WIDTH(\d+)-(.+)\]', r'[\2?\1]'])

    # Allow resizing images by changing
    # [filename.png?width] to [WIDTHwidth-filename.png]
    img_ext = r'png|jpe?g|gif|eps|bmp'
    img_name = r'\S.*\S|\S'

    # Apply this prepoc only after the latex image quotes have been added
    config['preproc'].append([r'\[(%s\.(%s))\?(\d+)\]' % (img_name, img_ext), r'[WIDTH\3-\1]'])

    return config


def convert(txt, target, headers=None, options=None):
    '''
    Code partly taken from txt2tags tarball
    '''
    add_mathjax = FORMULAS_SUPPORTED and 'html' in target and '$' in txt

    # Here is the marked body text, it must be a list.
    txt = txt.split('\n')

    # Only add MathJax code if there is a formula.
    if add_mathjax:
        if all(line.count('$') < 2 for line in txt):
            add_mathjax = False
    logging.debug('add_mathjax: %s' % add_mathjax)

    # Set the three header fields
    if headers is None:
        if target == 'tex':
            # LaTeX requires a title if \maketitle is used
            headers = ['RedNotebook', '', '']
        else:
            headers = ['', '', '']

    config = _get_config(target)

    # MathJax
    if add_mathjax:
        config['postproc'].append([r'</body>', MATHJAX + '</body>'])

    config['outfile'] = txt2tags.MODULEOUT  # results as list
    config['target'] = target

    if options is not None:
        config.update(options)

    # Let's do the conversion
    try:
        headers   = txt2tags.doHeader(headers, config)
        body, toc = txt2tags.convert(txt, config)
        footer  = txt2tags.doFooter(config)
        toc = txt2tags.toc_tagger(toc, config)
        toc = txt2tags.toc_formatter(toc, config)
        full_doc  = headers + toc + body + footer
        finished  = txt2tags.finish_him(full_doc, config)
        result = '\n'.join(finished)

    # Txt2tags error, show the messsage to the user
    except txt2tags.error, msg:
        logging.error(msg)
        result = msg

    # Unknown error, show the traceback to the user
    except:
        result = txt2tags.getUnknownErrorMessage()
        logging.error(result)
    return result


def convert_to_pango(txt, headers=None, options=None):
    '''
    Code partly taken from txt2tags tarball
    '''
    original_txt = txt

    # Here is the marked body text, it must be a list.
    txt = txt.split('\n')

    # Set the three header fields
    if headers is None:
        headers = ['', '', '']

    config = txt2tags.ConfigMaster()._get_defaults()

    config['outfile'] = txt2tags.MODULEOUT  # results as list
    config['target'] = 'xhtml'

    config['preproc'] = []
    # We need to escape the ampersand here, otherwise "&amp;" would become
    # "&amp;amp;"
    config['preproc'].append([r'&amp;', '&'])

    # Allow line breaks
    config['postproc'] = []
    config['postproc'].append([REGEX_LINEBREAK, '\n'])

    if options is not None:
        config.update(options)

    # Let's do the conversion
    try:
        body, toc = txt2tags.convert(txt, config)
        full_doc  = body
        finished  = txt2tags.finish_him(full_doc, config)
        result = ''.join(finished)

    # Txt2tags error, show the messsage to the user
    except txt2tags.error, msg:
        logging.error(msg)
        result = msg

    # Unknown error, show the traceback to the user
    except:
        result = txt2tags.getUnknownErrorMessage()
        logging.error(result)

    # remove unwanted paragraphs
    result = result.replace('<p>', '').replace('</p>', '')

    logging.log(5, 'Converted "%s" text to "%s" txt2tags markup' %
                (repr(original_txt), repr(result)))

    # Remove unknown tags (<a>)
    def replace_links(match):
        """Return the link name."""
        return match.group(1)
    result = re.sub(REGEX_HTML_LINK, replace_links, result)

    try:
        attr_list, plain, accel = pango.parse_markup(result)

        # result is valid pango markup, return the markup
        return result
    except gobject.GError:
        # There are unknown tags in the markup, return the original text
        logging.debug('There are unknown tags in the markup: %s' % result)
        return original_txt


def convert_from_pango(pango_markup):
    original_txt = pango_markup
    replacements = dict((('<b>', '**'), ('</b>', '**'),
                        ('<i>', '//'), ('</i>', '//'),
                        ('<s>', '--'), ('</s>', '--'),
                        ('<u>', '__'), ('</u>', '__'),
                        ('&amp;', '&'),
                        ('&lt;', '<'), ('&gt;', '>'),
                        ('\n', r'\\'),
                        ))
    for orig, repl in replacements.items():
        pango_markup = pango_markup.replace(orig, repl)

    logging.log(5, 'Converted "%s" pango to "%s" txt2tags' %
                (repr(original_txt), repr(pango_markup)))
    return pango_markup


if __name__ == '__main__':
    from rednotebook.util.utils import show_html_in_browser
    markup = 'Aha\n\tThis is a quote. It looks very nice. Even with many lines'
    html = convert(markup, 'xhtml')
    show_html_in_browser(html, '/tmp/test.html')