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

import os

import gtk

from rednotebook.util import filesystem
from rednotebook.util import dates


WEEKDAYS = (_('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
            _('Friday'), _('Saturday'), _('Sunday'))


example_text = '''\
=== This is an example template ===

It has been created to show you what can be put into a template. \
To edit it, click the arrow right of "Template" \
and select the template under "Edit Template".

Templates can contain any formatting or content that is also \
allowed in normal entries.

Your text can be:

- **bold**
- //italic//
- __underlined__
- --strikethrough--
- or some **//__combination__//**


You can add images to your template:

**Images:** [""/path/to/your/picture"".jpg]

You can link to almost everything:

- **links to files on your computer:** [filename.txt ""/path/to/filename.txt""]
- **links to directories:** [directory name ""/path/to/directory/""]
- **links to websites:** [RedNotebook Homepage ""http://rednotebook.sourceforge.net""]


As you see, **bullet lists** are also available. As always you have to add two \
empty lines to end a list.

Additionally you can have **titles** and **horizontal lines**:

= Title level 1 =
(The dates in the export will use this level, so it is recommended to use lower
levels in your entries)
== Title level 2 ==
=== Title level 3 ===
etc.

====================

% Commentary text can be put on lines starting with a percent sign.
% Those lines will not show up in the preview and the export.

**Macros**:

When a template is inserted, every occurence of "$date$" is converted to \
the current date. You can set the date format in the preferences.

There is even more markup that you can put into your templates. Have a look at
the inline help (Ctrl+H) for information.
'''

help_text = '''\
Besides templates for weekdays you can also have arbitrary named templates.
For example you might want to have a template for "Meeting" or "Journey".
All templates must reside in the directory "%s".

The template button gives you the options to create a new template or to \
visit the templates directory.
'''

meeting = _('''\
=== Meeting ===

Purpose, date, and place

**Present:**
+
+
+


**Agenda:**
+
+
+


**Discussion, Decisions, Assignments:**
+
+
+
==================================
''')

journey = _('''\
=== Journey ===
**Date:**

**Location:**

**Participants:**

**The trip:**
First we went to xxxxx then we got to yyyyy ...

**Pictures:** [Image folder ""/path/to/the/images/""]
''')

call = _('''\
==================================
=== Phone Call ===
- **Person:**
- **Time:**
- **Topic:**
- **Outcome and Follow up:**
==================================
''')

personal = _('''\
=====================================
=== Personal ===

+
+
+
========================

**How was the Day?**


========================
**What needs to be changed?**
+
+
+
=====================================
''')


class TemplateManager(object):
    def __init__(self, main_window):
        self.main_window = main_window

        self.dirs = main_window.journal.dirs

        self.merge_id = None
        self.actiongroup = None

    def on_insert(self, action):
        title = action.get_name()

        # strip 'Insert'
        title = title[6:]

        if title == 'Weekday':
            text = self.get_weekday_text()
        else:
            text = self.get_text(title)
        self.main_window.day_text_field.insert(text)

    def on_edit(self, action):
        '''
        Open the template file in an editor
        '''
        edit_title = action.get_name()
        title = edit_title[4:]

        if title == 'Weekday':
            date = self.main_window.journal.date
            week_day_number = date.weekday() + 1
            title = str(week_day_number)

        filename = self.titles_to_files.get(title)
        filesystem.open_url(filename)

    def on_new_template(self, action):
        dialog = gtk.Dialog(_('Choose Template Name'))
        dialog.set_transient_for(self.main_window.main_frame)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

        entry = gtk.Entry()
        entry.set_size_request(300, -1)
        dialog.get_content_area().pack_start(entry)
        dialog.show_all()
        response = dialog.run()
        dialog.hide()

        if response == gtk.RESPONSE_OK:
            title = entry.get_text()
            if not title.lower().endswith('.txt'):
                title += '.txt'
            filename = os.path.join(self.dirs.template_dir, title)

            filesystem.make_file(filename, example_text)

            filesystem.open_url(filename)

    def on_open_template_dir(self):
        filesystem.open_url(self.dirs.template_dir)

    def get_template_file(self, basename):
        return os.path.join(self.dirs.template_dir, str(basename) + '.txt')

    def get_text(self, title):
        filename = self.titles_to_files.get(title, None)
        if not filename:
            return ''

        text = filesystem.read_file(filename)

        # An Error occured
        if not text:
            text = ('This template contains no text or has unreadable content. To edit it, '
                    'click the arrow right of "Template" '
                    'and select the template under "Edit Template".')

        # convert every "$date$" to the current date
        config = self.main_window.journal.config
        format_string = config.read('dateTimeString', '%A, %x %X')
        date_string = dates.format_date(format_string)

        template_text = text.replace(u'$date$', date_string)
        return template_text

    def get_weekday_text(self, date=None):
        if date is None:
            date = self.main_window.journal.date
        week_day_number = date.weekday() + 1
        return self.get_text(str(week_day_number))

    def get_available_template_files(self):
        dir = self.dirs.template_dir
        files = os.listdir(dir)
        files = map(lambda basename: os.path.join(dir, basename), files)

        # No directories allowed
        files = filter(lambda file:os.path.isfile(file), files)

        # No tempfiles
        files = filter(lambda file: not file.endswith('~'), files)
        return files

    def get_menu(self):
        '''
        See http://www.pygtk.org/pygtk2tutorial/sec-UIManager.html for help
        A popup menu cannot show accelerators (HIG).
        '''
        # complete paths
        files = self.get_available_template_files()

        def escape_name(name):
            """Remove special xml chars for GUI display."""
            for char in '&<>\'"':
                name = name.replace(char, '')
            return name

        # 1, 2, 3
        self.titles_to_files = {}
        for file in files:
            root, ext = os.path.splitext(file)
            title = os.path.basename(root)
            self.titles_to_files[escape_name(title)] = file

        sorted_titles = sorted(self.titles_to_files.keys())

        menu_xml = '''\
        <ui>
        <popup action="TemplateMenu">'''

        insert_menu_xml = '''
            <menu action="InsertMenu">
                <menuitem action="InsertWeekday"/>
                <separator name="sep4"/>'''
        for title in sorted_titles:
            if title not in map(str, range(1, 8)):
                insert_menu_xml += '''
                <menuitem action="Insert%s"/>''' % title
        insert_menu_xml += '''
            </menu>'''

        menu_xml += insert_menu_xml

        menu_xml += '''
            <separator name="sep5"/>
            <menuitem action="NewTemplate"/>'''

        edit_menu_xml = '''
            <menu action="EditMenu">
                <menuitem action="EditWeekday"/>
                <separator name="sep3"/>'''
        for title in sorted_titles:
            if title not in map(str, range(1,8)):
                edit_menu_xml += '''
                <menuitem action="Edit%s"/>''' % title
        edit_menu_xml += '''
            </menu>'''

        menu_xml += edit_menu_xml

        menu_xml +='''
            <menuitem action="OpenTemplateDirectory"/>
        </popup>
        </ui>'''

        uimanager = self.main_window.uimanager

        if self.actiongroup:
            uimanager.remove_action_group(self.actiongroup)

        # Create an ActionGroup
        self.actiongroup = gtk.ActionGroup('TemplateActionGroup')

        # Create actions
        actions = []

        for title in sorted_titles:
            insert_action = ('Insert' + title, None, title, None, None,
                    lambda widget: self.on_insert(widget))
            actions.append(insert_action)
            edit_action = ('Edit' + title, None, title, None, None,
                    lambda widget: self.on_edit(widget))
            actions.append(edit_action)

        actions.append(('InsertWeekday', gtk.STOCK_HOME,
                        _("This Weekday's Template"), None, None,
                        lambda widget: self.on_insert(widget)))

        actions.append(('EditMenu', gtk.STOCK_EDIT, _('Edit Template'), None,
                        None, None))

        actions.append(('InsertMenu', gtk.STOCK_ADD, _('Insert Template'), None,
                        None, None))

        actions.append(('EditWeekday', gtk.STOCK_HOME, _("This Weekday's Template"),
                    None, None, lambda widget: self.on_edit(widget)))

        actions.append(('NewTemplate', gtk.STOCK_NEW, _('Create New Template'),
                    None, None, lambda widget: self.on_new_template(widget)))

        actions.append(('OpenTemplateDirectory', gtk.STOCK_DIRECTORY,
                    _('Open Template Directory'), None, None,
                    lambda widget: self.on_open_template_dir()))

        self.actiongroup.add_actions(actions)

        # Remove the lasts ui description
        if self.merge_id:
            uimanager.remove_ui(self.merge_id)

        # Add a UI description
        self.merge_id = uimanager.add_ui_from_string(menu_xml)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(self.actiongroup, 0)

        # Create a Menu
        menu = uimanager.get_widget('/TemplateMenu')
        return menu

    def make_empty_template_files(self):
        global help_text

        files = []
        for day_number in range(1, 8):
            weekday = WEEKDAYS[day_number - 1]
            files.append((self.get_template_file(day_number),
                          example_text.replace('template ===',
                                               'template for %s ===' % weekday)))

        help_text %= (self.dirs.template_dir)

        files.append((self.get_template_file('Help'), help_text))

        # Only add the example templates the first time and just restore
        # the day templates everytime
        if self.main_window.journal.is_first_start:
            files.append((self.get_template_file('Meeting'), meeting))
            files.append((self.get_template_file('Journey'), journey))
            files.append((self.get_template_file('Call'), call))
            files.append((self.get_template_file('Personal'), personal))

        filesystem.make_files(files)