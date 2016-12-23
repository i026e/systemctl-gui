#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 17:01:46 2016

@author: pavel
"""
import sys
sys.path.append( "../" )

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL) #handle Ctrl-C

import logging
import threading

#from systemd.manager import Manager

import systemctl_commands as stl

GLADE_FILE = "gui.glade"
APP = "mime-editor-gui"

#FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
Logger = logging.getLogger(APP)
Logger.setLevel(logging.DEBUG)

"""
class UnitWrapper(GObject.GObject):
    def __init__(self, systemd_unit):
        GObject.GObject.__init__(self)
        self.systemd_unit = systemd_unit        
        self.id_ = bytes(systemd_unit.properties.Id, "utf-8").decode("unicode_escape") 
        
        Logger.debug("Processing %s", self.id_)
        
    def __getattr__(self, attr):
        val = self.systemd_unit.__dict__.get(attr)
        Logger.debug("%s: %s=%s", self.id_, attr, val)
        return val
        
    def is_active(self):        
        Logger.debug("%s is %s", self.id_, self.systemd_unit.properties.ActiveState)
        return "active" == self.systemd_unit.properties.ActiveState
        
    def is_loaded(self):
        Logger.debug("%s is %s", self.id_, self.systemd_unit.properties.LoadState)
        return "loaded" == self.systemd_unit.properties.LoadState
        
    def stop(self):
        try:
            self.systemd_unit.stop("replace")
        except Exception as e:
            Logger.error("Error when stopping %s:\n\n%s", self.id_, e)
            
    def start(self):
        try:
            self.systemd_unit.start("fail")
        except Exception as e:
            Logger.error("Error when starting %s:\n\n%s", self.id_, e)
            
    def change_active(self):
        if self.is_active():
            self.stop()
        else:
            self.start()
"""

def async_method(func):
    def start(*args, **kwargs):
        thr = threading.Thread(target = func, args = args, kwargs = kwargs)
        thr.start()
    return start
        
class UnitWrapper(GObject.GObject):
    stl_commands = {"stop" : stl.stop,
                    "start" : stl.start,
                    "restart" : stl.restart,
                    "kill" : stl.kill,
                    "disable" : stl.disable,
                    "enable": stl.enable,
                    "reload" : stl.reload,   
                    "status" : stl.get_status,
                    "dependencies" : stl.get_dependencies,
                    "properties": stl.get_properties}
                    
    def __init__(self, unit_id, *args):
        GObject.GObject.__init__(self)
        Logger.debug("Processing %s", unit_id)
        
        self.id_ = unit_id
        self.descr = stl.get_description(unit_id) 
        
        self.update_status()
        
    def execute(self, command):
        result = None
        if command in self.stl_commands:
            try:            
                result = self.stl_commands.get(command)(self.id_)
            except Exception as e:
                Logger.error("%s %s():\n%s\n", self.id_, command, e)
            finally:
                self.update_status()
        return result           
        
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
            
class ServicesView():
    def __init__(self, builder, model, context_menu, details_window):
        self.builder = builder
        self.model = model
        self.context_menu = context_menu
        self.details_window = details_window
        
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
        
        Logger.info("active flag toggled for %s", unit.id_)
        Logger.debug("active flag state (%s)", renderer.get_active())
        
        unit.change_active()
        
        self.model.update_unit_at_path(str_path)
        
    def _on_enable_flag_toggled(self, renderer, str_path, *data):        
        unit = self.model.get_unit_at_path(str_path)
        
        Logger.info("loaded flag toggled for %s", unit.id_)
        Logger.debug("loaded flag state (%s)", renderer.get_active())

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
        
class DetailsWindow:
    def __init__(self, builder, model, parent_window):
        self.builder = builder
        self.model = model
        
        self.window = self.builder.get_object("details_window")
        self.window.connect("delete-event", self.on_hide)
        self.window.set_transient_for(parent_window)
        
        self.__init_buttons()
        self.__init_widgets()
        
        self.current_path = 0    
        self.current_unit = None
        
    def __init_widgets(self):
        self.id_label = self.builder.get_object("details_id_label")
        self.status_view = self.builder.get_object("details_status_view")
        self.dep_view = self.builder.get_object("details_depend_view")
        self.prop_view = self.builder.get_object("details_prop_view")       
        
        
    def __init_buttons(self):
        self.ok_button = self.builder.get_object("details_ok_button")
        self.ok_button.connect("clicked", self.on_hide)
        
        
    def show(self, path):
        self.current_path = path        
        self.current_unit = self.model.get_unit_at_path(self.current_path)
        
        if self.current_unit is not None:
            self._update_widgets()            
        
        self.ok_button.grab_focus()    
        self.window.show()
        
    def _update_widgets(self):
        self.id_label.set_text(self.current_unit.id_)
        self._set_status()
        self._set_dependencies()
        self._set_properties()
        
    def _set_text(self, textview, text):
        textview.get_buffer().set_text(text)
        return False #!!! For idle_add
        
    @async_method    
    def _set_status(self):
        status = self.current_unit.execute("status")
        GObject.idle_add(self._set_text, self.status_view , status)

    @async_method    
    def _set_dependencies(self):
        dependencies = self.current_unit.execute("dependencies")
        GObject.idle_add(self._set_text, self.dep_view, dependencies)
        
    @async_method
    def  _set_properties(self):
        properties = self.current_unit.execute("properties")
        GObject.idle_add(self._set_text, self.prop_view, properties)       
        
        
    def on_hide(self, *args):
        self.current_unit = None
        self.window.hide()
        return True #!!! otherwise segfault on next show
        
        
        
class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APP)
        self.builder.add_from_file(GLADE_FILE)

        self.window = self.builder.get_object("main_window")
        self.window.connect("delete-event", self.on_close)
        
        self.model = ServicesDataModel()
        self.details_window = DetailsWindow(self.builder, self.model, self.window)
        
        self.context_menu = ContextMenu(self.builder, self.model, 
                                        self.details_window)        
                
        
        self.view = ServicesView(self.builder, self.model, 
                                 self.context_menu, self.details_window)
        
    def run(self):
        self.window.show()
        Gtk.main()
    
    def on_close(self, *args):
        Gtk.main_quit()
        
    
    
if __name__ == "__main__":

    window = MainWindow()
    window.run()    
