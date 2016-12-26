#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 17:01:46 2016

@author: pavel
"""
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C



#from systemd.manager import Manager

import systemctl_commands as stl
import app_launcher
import utils
from utils import logger, async_method

from details_gui import DetailsWindow
from about_gui import AboutDialog



GLADE_FILE = "gui.glade"
        
class UnitWrapper(GObject.GObject):
    def __init__(self, unit_id, *args):
        GObject.GObject.__init__(self)
        logger.debug("Processing %s", unit_id)
        
        self.id_ = unit_id
        self.descr = stl.get_description(unit_id) 
        
        self.update_status()
        
    def execute(self, command):
        return stl.execute(self.id_, command)
        
    def get_content(self):
        return stl.get_content(self.id_)
        
    def get_properties(self):
        return stl.get_properties(self.id_)
        
    def get_status(self):
        return stl.get_status(self.id_)

    def get_dependencies(self):
        return stl.get_dependencies(self.id_)        
        
    def update_status(self):
        self.active = stl.is_active(self.id_)
        self.enabled = stl.is_enabled(self.id_)
            
    def change_active(self):
        if self.active:
            self.execute("stop")
        else:
            self.execute("start") 
            
    def change_enabled(self):
        if self.enabled:
            self.execute("disable")
        else:
            self.execute("enable")

        
class TextColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, tooltip_text, model_index_txt,  
                                                             *args, **kwargs):
        super(TextColumn, self).__init__(*args, **kwargs)
        
        self.title = Gtk.Label(column_name)
        self.title.set_tooltip_text(tooltip_text)
        self.title.show()
        self.set_widget(self.title)        
        
        renderer_text = Gtk.CellRendererText()
        self.cell_renderers = (renderer_text, )

        self.pack_start(renderer_text, expand = True)
        self.add_attribute(renderer_text, "text", model_index_txt)

        self.set_resizable(True)

    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)
            
class FlagColumn(Gtk.TreeViewColumn):
    def __init__(self, column_name, tooltip_text, model_index_bool, 
                 on_toggle, *args, on_toggle_data=None ,**kwargs):
        super(FlagColumn, self).__init__(*args, **kwargs)
        
        self.title = Gtk.Label(column_name)
        self.title.set_tooltip_text(tooltip_text)
        self.title.show()        
        self.set_widget(self.title)

        renderer_flag = Gtk.CellRendererToggle()
        self.cell_renderers = (renderer_flag, )

        renderer_flag.connect("toggled", on_toggle, on_toggle_data)

        self.pack_start(renderer_flag, expand = False)
        self.add_attribute(renderer_flag, "active", model_index_bool)

        self.set_clickable(True)
        self.set_resizable(False)        

        #self.set_sort_indicator(True)

    def set_attribute(self, name, model_column):
        for renderer in self.cell_renderers:
            self.add_attribute(renderer, name, model_column)

class ServicesDataModel():
    UNIT_COL = 0 #UnitWrapper
    UNIT_ID_COL = 1 #str
    UNIT_DESC_COL = 2 #str
    UNIT_IS_ENABLED_COL = 3 #bool
    UNIT_IS_ACTIVE_COL = 4 #bool
    #UNIT_PATH_COL = 5 #str
    # unit, name, description, loaded, active, path
    LIST_STORE_COLUMN_TYPES = [UnitWrapper, str, str, bool, bool,]# str]
    
    def __init__(self):        
        
        #list_store -> filter -> sort
        self.list_store = Gtk.ListStore(*self.LIST_STORE_COLUMN_TYPES)
        self.filter_model = self.list_store.filter_new()
        self.filter_model.set_visible_func(self.__filter_func, data=None)
        self.sortable_model = Gtk.TreeModelSort(self.filter_model)
        
        #
        self.__load_data()
        
    def get_model(self):
        return self.sortable_model
        
    def __filter_func(self, model, iter_, data):
        #TODO:
        return True
        
    def __get_unit_data(self, unit):
         id_ = unit.id_
         descr = unit.descr
         is_enabled = unit.enabled
         is_active = unit.active         
         
         return [unit, id_, descr, is_enabled, is_active]

    @async_method    
    def __load_data(self):
        def append(data):
            self.list_store.append(data)
            return False #for idle_add
        
        for unit, status in stl.list_units():
            wrapped_unit = UnitWrapper(unit, status)
            unit_data = self.__get_unit_data(wrapped_unit)
            GObject.idle_add(append, unit_data)            

            
    def __get_store_path(self, sorted_path):
        """ get list store model path
            from sortable model path
        """
        # sorted_path -> filtered_path -> store_path
        if type(sorted_path) != Gtk.TreePath:
            sorted_path = Gtk.TreePath.new_from_string(sorted_path)
        filtered_path = self.sortable_model.convert_path_to_child_path(sorted_path)   
        store_path = self.filter_model.convert_path_to_child_path(filtered_path)
        return store_path
            
    def __get_iter(self, sorted_path):        
        store_path = self.__get_store_path(sorted_path)
        iter_ = self.list_store.get_iter(store_path)
        return iter_
            
    def get_unit_at_path(self, sorted_path):
        iter_ = self.__get_iter(sorted_path)
        return self.list_store.get_value(iter_, self.UNIT_COL)
        
    def update_unit_at_path(self, sorted_path):
        iter_ = self.__get_iter(sorted_path)
        unit = self.list_store.get_value(iter_, self.UNIT_COL)
        
        for col, val in enumerate(self.__get_unit_data(unit)):
            self.list_store.set_value(iter_, col, val)
            
    def reload(self):
        self.list_store.clear()
        self.__load_data()
        
class ContextMenu():
    UNIT_ACTION_MENUITEMS = {"start_menuitem" : "start",
                             "stop_menuitem" : "stop",
                             "restart_menuitem" : "restart",
                             "kill_menuitem" : "kill",
                             "enable_menuitem" : "enable",
                             "disable_menuitem" : "disable",
                             "reload_menuitem" : "reload" }
                             
    UNIT_ACTION_VISIBILITY = {"start_menuitem" : lambda unit : not unit.active,
                             "stop_menuitem" : lambda unit : unit.active,
                             "restart_menuitem" : lambda unit : unit.active,
                             "kill_menuitem" : lambda unit : unit.active,
                             "enable_menuitem" :lambda unit : not unit.enabled,
                             "disable_menuitem" : lambda unit : unit.enabled
                             }
    
    
    def __init__(self, builder, model, details_window):
        self.builder = builder  
        self.model = model
        self.details_window = details_window
        self.current_path = 0    
        self.current_unit = None
        
        self.context_menu = self.builder.get_object("popup_menu")        
        
        self.menuitem_details = self.builder.get_object("details_menuitem")
        self.menuitem_details.connect("activate", self._on_menuitem_details)        
        
        self.unit_menuitems = {}
        for name, action in ContextMenu.UNIT_ACTION_MENUITEMS.items():
            item = self.builder.get_object(name)
            item.connect("activate", self._on_unit_action_activated, action)
            self.unit_menuitems[name] = item    
              
    def show(self, path, widget, event):
        self.current_path = path
        self.current_unit = self.model.get_unit_at_path(self.current_path)
        
        self._hide_actions()      
        
        self.context_menu.popup( None, None, None, None, 0, event.time)
        
        
    def _hide_actions(self):
        if self.current_unit is not None:
            for name, item in self.unit_menuitems.items():
                if name in ContextMenu.UNIT_ACTION_VISIBILITY:
                    func = ContextMenu.UNIT_ACTION_VISIBILITY.get(name)
                    item.set_visible(func(self.current_unit))
        
    def _on_unit_action_activated(self, menuitem, action):
        if self.current_unit is  not None:
            self.current_unit.execute(action)
            self.model.update_unit_at_path(self.current_path)
            
        self.current_unit = None
        
    def _on_menuitem_details(self, menuitem):
        if self.current_unit is not None:
            self.details_window.show(self.current_path)
            

        
class ServicesView:
    def __init__(self, builder, model, details_window):
        self.builder = builder
        self.model = model        
        self.details_window = details_window
        self.context_menu = ContextMenu(self.builder, self.model, 
                                        self.details_window) 
        
        self.__init_view()
        self.__add_columns()
        
        
        
    def __init_view(self):
        self.view = self.builder.get_object("services_view")
        self.view.set_model(self.model.get_model()) 
        self.view.set_tooltip_column(self.model.UNIT_DESC_COL)
        
        self.view.connect("button-press-event", self._on_mouse_clicked)        
        self.view.connect("key-press-event", self._on_key_pressed)

        self.selection =  self.view.get_selection()        
        
        
    def __add_columns(self):
        enabled_column = FlagColumn("startup", "loaded",
                                   self.model.UNIT_IS_ENABLED_COL,
                                   self._on_enable_flag_toggled)
        enabled_column.set_sort_column_id(self.model.UNIT_IS_ENABLED_COL)
        self.view.append_column(enabled_column)
        
        active_column = FlagColumn("active", "active",
                                   self.model.UNIT_IS_ACTIVE_COL,
                                   self._on_active_flag_toggled)
        active_column.set_sort_column_id(self.model.UNIT_IS_ACTIVE_COL)
        self.view.append_column(active_column)
        
        name_column = TextColumn("unit", "unit",
                                 self.model.UNIT_ID_COL)
        name_column.set_sort_column_id(self.model.UNIT_ID_COL)
        self.view.append_column(name_column)
    
    def _show_context_menu(self, widget, event):
        if self.selection.count_selected_rows() >= 1:
            path = self.selection.get_selected_rows()[1][0]            
            self.context_menu.show(path, widget, event)
            
    def _show_details_window(self, widget, event):
        if self.selection.count_selected_rows() >= 1:
            path = self.selection.get_selected_rows()[1][0]
            self.details_window.show(path)
        
        
    def _on_active_flag_toggled(self, renderer, str_path, *data):        
        unit = self.model.get_unit_at_path(str_path)
        
        logger.info("active flag toggled for %s", unit.id_)
        logger.debug("active flag state (%s)", renderer.get_active())
        
        unit.change_active()
        
        self.model.update_unit_at_path(str_path)
        
    def _on_enable_flag_toggled(self, renderer, str_path, *data):        
        unit = self.model.get_unit_at_path(str_path)
        
        logger.info("loaded flag toggled for %s", unit.id_)
        logger.debug("loaded flag state (%s)", renderer.get_active())

        unit.change_enabled()
        
        self.model.update_unit_at_path(str_path)         
        
    def _on_mouse_clicked(self, widget, event):
        if event.button == 3: #right button
            self._show_context_menu(widget, event)
            return False
        elif event.type == Gdk.EventType._2BUTTON_PRESS: #double click
            self._show_details_window(widget, event)
            return False
           
    def _on_key_pressed(self, widget, event):
        #do not reset selection
        keyname = Gdk.keyval_name(event.keyval)       

        if keyname in {"Menu"}:
            self._show_context_menu(widget, event)
            return True
        elif keyname in {"Return"}:
            self._show_details_window(widget, event)
            return True
           
       
class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(utils.APP)
        self.builder.add_from_file(GLADE_FILE)

        self.window = self.builder.get_object("main_window")
        self.window.connect("delete-event", self._on_close)
        
        self.model = ServicesDataModel()
        self.details_window = DetailsWindow(self.builder, self.model, self.window)
        self.view = ServicesView(self.builder, self.model, 
                                 self.details_window)
        
        self.__init_menu()
        
    def __init_menu(self):
        menuitem_quit = self.builder.get_object("file_quit_menuitem")
        menuitem_quit.connect("activate", self._on_close)
        
        menuitem_reload = self.builder.get_object("view_reload_menuitem")
        menuitem_reload.connect("activate", self._on_reload)
        
        menuitem_log = self.builder.get_object("view_log_menuitem")
        menuitem_log.connect("activate", self._on_log)
        
        menuitem_about = self.builder.get_object("help_about_menuitem")
        menuitem_about.connect("activate", self._on_about)
        
        menuitem_man = self.builder.get_object("help_manual_menuitem")
        menuitem_man.connect("activate", self._on_manual)
        
    def run(self):
        self.window.show()
        Gtk.main()
    
    def _on_close(self, *args):
        Gtk.main_quit()
        
    def _on_reload(self, *args):
        stl.daemon_reload()
        self.model.reload()
        
    def _on_log(self, *args):
        pass
    
    def _on_about(self, *args):
        AboutDialog(self.builder, self.window).show()
    
    @async_method
    def _on_manual(self, *args):
        def on_man_close(page):
            logger.info("Help page %s", page)
        app_launcher.Browser.systemctl_man(on_man_close)
        
    
    
if __name__ == "__main__":

    window = MainWindow()
    window.run()    
