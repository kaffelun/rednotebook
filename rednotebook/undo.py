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

from collections import defaultdict
import logging


class Action(object):
    def __init__(self, undo_function, redo_function, tags):
        self.undo_function = undo_function
        self.redo_function = redo_function
        self.tags = tags


class UndoRedoManager(object):
    size = 100
    buffer = 20

    def __init__(self, main_window):
        self.main_window = main_window

        self.undo_menu_item = self.main_window.uimanager.get_widget('/MainMenuBar/Edit/Undo')
        self.redo_menu_item = self.main_window.uimanager.get_widget('/MainMenuBar/Edit/Redo')

        self.undo_stacks = defaultdict(list)
        self.redo_stacks = defaultdict(list)

        self.date = None

    @property
    def undo_stack(self):
        return self.undo_stacks[self.date]

    @property
    def redo_stack(self):
        return self.redo_stacks[self.date]

    def set_date(self, date):
        self.date = date
        self.update_buttons()

    def add_action(self, action):
        '''
        Arguments are functions that encode what there is to to to redo and undo
        the action
        '''
        self.undo_stack.append(action)

        # Delete some items, if the undo stack grows too big
        if len(self.undo_stack) > self.size + self.buffer:
            del self.undo_stack[:self.buffer]

        # When a new action has been made, forget all redos
        del self.redo_stack[:]

        self.update_buttons()

    def undo(self, *args):
        if not self.can_undo():
            logging.info('There is nothing to undo')
            return

        logging.debug('Undo')

        action = self.undo_stack.pop()
        action.undo_function()
        self.redo_stack.append(action)

        self.update_buttons()

    def redo(self, *args):
        if not self.can_redo():
            logging.info('There is nothing to redo')
            return

        logging.debug('Redo')

        action = self.redo_stack.pop()
        action.redo_function()
        self.undo_stack.append(action)

        self.update_buttons()

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def update_buttons(self):
        self.undo_menu_item.set_sensitive(self.can_undo())
        self.redo_menu_item.set_sensitive(self.can_redo())