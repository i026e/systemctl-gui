#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 26 10:46:52 2016

@author: pavel
"""
import os
import sys
import systemctl_commands as stl

from gi.repository import Gtk
from utils import Singleton


class AboutDialog(metaclass=Singleton):
    def __init__(self, builder, parent_window):
        self.builder = builder
        self.dialog = self.builder.get_object("about_window")
        self.dialog.connect("delete-event", self._on_hide)
        self.dialog.set_transient_for(parent_window)

        self.__init_view()

    def __init_view(self):
        self.view =  self.builder.get_object("about_view")
        template="OS: {os_ver} \n\n Python: {python_ver} \n\n Gtk: {gtk_ver} \n\n systemctl: {stl_ver}"

        python_ver = sys.version

        uname = os.uname()
        os_ver = "{sysname} {machine} {release} {version} {nodename}".format(\
        nodename = uname.nodename, sysname = uname.sysname,\
        machine = uname.machine, release=uname.release, version=uname.version)

        gtk_ver = "{major}.{minor}.{micro}".format(\
        major=Gtk.get_major_version(), minor= Gtk.get_minor_version(),\
        micro = Gtk.get_micro_version())

        stl_ver = stl.get_systemctl_version()

        text = template.format(os_ver=os_ver, python_ver=python_ver,
                               stl_ver=stl_ver, gtk_ver=gtk_ver)


        self.dialog.set_comments(text)


    def show(self):
        response = self.dialog.run()
        self._on_hide()

    def _on_hide(self, *args):
        self.dialog.hide()
        return True
