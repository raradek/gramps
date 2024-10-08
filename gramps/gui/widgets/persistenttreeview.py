#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2021  Serge Noiraud
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
An override to allow resizable columns
"""
import logging

from gi.repository import Gtk
from gramps.gen.config import config
from gramps.gui.views.treemodels.flatbasemodel import FlatBaseModel

_LOG = logging.getLogger(".persistent")

# -------------------------------------------------------------------------
#
# PersistentTreeView class
#
# -------------------------------------------------------------------------

__all__ = ["PersistentTreeView"]


class PersistentTreeView(Gtk.TreeView):
    """
    TreeView that has resizable columns
    """

    __gtype_name__ = "PersistentTreeView"

    def __init__(self, uistate=None, config_name=None):
        """
        Create a TreeView widgets with column size saving
        """
        Gtk.TreeView.__init__(self)
        self.config_name_spacing = "undefined"
        self.connect("destroy", self.save_column_info)
        self.uistate = None
        if uistate:
            self.set_uistate(uistate)
        if config_name:
            self.set_config_name(config_name)

    def set_uistate(self, uistate):
        """
        parameter: uistate: The associated uistate
        This parameter is used to connect some signals from this class.
        """
        if not self.uistate and uistate:
            _LOG.debug("connect signal font-changed")
            uistate.connect("font-changed", self.restore_columns)
            self.uistate = uistate

    def set_config_name(self, name):
        """
        parameter: name: The associated config name string for the treeview
        This parameter must be unique as it allow the tab columns size saving
        """
        # Here, we can have:
        # name = gramps.gui.editors.displaytabs.personeventembedlist
        # The following line return only the last part of the string.
        # personeventembedlist in this case
        last = name.split(".")[-1]
        _LOG.debug("set persistent name : %s" % last)
        self.config_name_spacing = "spacing.%s" % last
        self.config_name_sorting = "sorting.%s" % last
        if not config.is_set(self.config_name_spacing):
            _LOG.debug("registering %s" % self.config_name_spacing)
            config.register(self.config_name_spacing, [])
        if not config.is_set(self.config_name_sorting):
            _LOG.debug("registering %s" % self.config_name_sorting)
            config.register(self.config_name_sorting, [])

    def set_model(self, model):
        super().set_model(model)
        if model is not None:
            self.restore_columns()

    def save_column_info(self, tree=None):
        """
        Save the columns width
        """
        if self.config_name_spacing == "undefined":
            return
        newsize = self.get_columns_size()
        if 0 not in newsize:
            # Don't save the values if one column size is null.
            config.set(self.config_name_spacing, newsize)
            _LOG.debug("save persistent : %s = %s" % (self.config_name_spacing, newsize))

        """
        Save the sorting column id
        """
        model = self.get_model()
        if model:
            if isinstance(model, FlatBaseModel):
                sortcol = model.sort_col
                sortdir = int(model._reverse)
            elif isinstance(model, (Gtk.TreeStore, Gtk.ListStore)):
                sortcol, sortdir = model.get_sort_column_id()
            else:
                _LOG.error("save persistent : not implemented for model %s" % (type(model)))
            
            if sortcol is not None:
                config.set(self.config_name_sorting, [sortcol, int(sortdir)])

        return

    def get_columns_size(self):
        """
        Get all the columns size
        """
        columns = self.get_columns()
        newsize = []
        nbc = 0
        context = Gtk.Label().get_pango_context()
        font_desc = context.get_font_description()
        char_width = 1.2 * (font_desc.get_size() / 1000)
        for column in columns:
            if nbc < len(columns) - 1 or len(columns) == 1:
                # Don't save the last column size, it's wrong
                # except if we have only one column (i.e. EditRule)
                child = column.get_widget()
                if isinstance(child, Gtk.Image):
                    # Don't resize the icons
                    size = 2
                else:
                    size = column.get_width() / char_width
                    size = 2 if size < 2 else size
                newsize.append(size)
            nbc += 1
        return newsize

    def restore_columns(self):
        """
        restore the columns width
        """
        if self.config_name_spacing == "undefined":
            return
        size = config.get(self.config_name_spacing)
        if len(size) == 0:
            _LOG.debug(
                "restore for the first time : %s = %s" % (self.config_name_spacing, size)
            )
            return
        _LOG.debug("restore persistent : %s = %s" % (self.config_name_spacing, size))
        context = Gtk.Label().get_pango_context()
        font_desc = context.get_font_description()
        char_width = 1.2 * (font_desc.get_size() / 1000)
        nbc = 0
        columns = self.get_columns()
        for column in columns:
            if nbc < len(size):
                column.set_fixed_width(size[nbc] * char_width)
            nbc += 1

        """
        Restore sorting
        """
        model = self.get_model()
        sort_config = config.get(self.config_name_sorting)
        if model and sort_config and sort_config[0] is not None:
            if isinstance(model, FlatBaseModel):
                model.sort_col = sort_config[0]
                model._reverse = sort_config[1]
            elif isinstance(model, (Gtk.TreeStore, Gtk.ListStore)):
                model.set_sort_column_id(sort_config[0], sort_config[1])