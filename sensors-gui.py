#!/usr/bin/env python3

"""
@author: Pavel Rojtberg (http://www.rojtberg.net)
@see: https://launchpad.net/sensors-unity
@copyright: GPLv3 <http://opensource.org/licenses/GPL-3.0>
"""

import gi
gi.require_version("Unity", "7.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Unity, GObject, Gtk, GLib

import os.path
from sensors import sensors
import json
import locale

DATA = "/usr/share/sensors-unity/"
#DATA = os.path.expanduser("~/workspace/sensors-unity/")

if "SNAP" in os.environ:
    DATA = os.environ["SNAP"] + DATA[4:] # $SNAP/share/..

GETTEXT_DOMAIN = "sensors-unity"
# use locale instead of gettext, so GTK gets the change
locale.bindtextdomain(GETTEXT_DOMAIN, DATA+"locale/")
locale.textdomain(GETTEXT_DOMAIN)
_ = locale.gettext

UNITS = {sensors.feature.TEMP: (int, "°C"), 
         sensors.feature.FAN: (int, "RPM"), 
         sensors.feature.IN: (float, "V")}
     
class Sensor:
    iter = None
    val = None
 
    def __init__(self, raw):
        self.raw = raw
        self._pytype, unit = UNITS[self.type()]
        self._fmt = "{:.3f} " if self._pytype is float else "{} "
        self._fmt += unit
    
    def read(self):
        self.val = self._pytype(sensors.get_value(self.raw[0], next(sensors.SubFeatureIterator(*self.raw)).number))
    
    def str_val(self):
        return self._fmt.format(self.val)
    
    def label(self):
        return sensors.get_label(*self.raw)
    
    def type(self):
        return self.raw[1].type
    
    def id(self):
        return (self.raw[0].prefix, self.raw[1].name)
    
class Controller:
    SENSORS_CONF = GLib.get_user_config_dir() + "/sensors3.conf"
    CONFIG_FILE = GLib.get_user_config_dir() + "/sensors-unity.json"
            
    # order controls display order
    DISPLAY_TYPES = (sensors.feature.TEMP, sensors.feature.FAN, sensors.feature.IN)
    
    # only allow monitoring integer types as label does not work with floats
    MONITOR_TYPES = (sensors.feature.TEMP, sensors.feature.FAN)
    
    MONITOR_NONE = (b"", b"")
    
    def __init__(self):
        xml = Gtk.Builder()
        xml.set_translation_domain(GETTEXT_DOMAIN)
        xml.add_from_file(DATA+"window.ui")
            
        about = xml.get_object("aboutdialog1")
        xml.get_object("menuitem_about").connect("activate", lambda *args: about.show())
        xml.connect_signals({"hide-widget": lambda w, *args: w.hide_on_delete()})
        
        window = xml.get_object("window1")
        window.connect("delete-event", self.end)
        
        cfg = None
        
        try:
            cfg = json.load(open(self.CONFIG_FILE))
        except ValueError:
            pass
        except FileNotFoundError:
            pass

        if cfg is not None:
            self.monitor = tuple(e.encode("utf-8") for e in cfg["monitor"])
            self.expanded = cfg["expanded"]
        else:
            self.monitor = self.MONITOR_NONE
            self.expanded = [True for t in self.DISPLAY_TYPES]
        
        self.le = Unity.LauncherEntry.get_for_desktop_file("sensors-unity.desktop")
        self.le.set_property("count-visible", True)
        
        # construct treeview       
        self.tstore = xml.get_object("treestore1")
        
        self.group = {}
        self.data = []
        
        for t, title in zip(self.DISPLAY_TYPES, (_("Thermal Sensors"), _("Fans"), _("Voltages"))):
            self.group[t] = self.tstore.append(None, ["<b>{}</b>".format(title), "", False, False])

        self.tview = xml.get_object("treeview1")
        renderer = Gtk.CellRendererText()
        renderer.set_fixed_height_from_font(1)
        
        column = Gtk.TreeViewColumn(_("Sensor"), renderer, markup=0)
        self.tview.append_column(column)
        
        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1, 0.5)
        renderer.set_fixed_height_from_font(1)
        
        column = Gtk.TreeViewColumn(_("Value"), renderer, text=1)
        self.tview.append_column(column)
        
        renderer = Gtk.CellRendererToggle()
        renderer.set_radio(True)
        renderer.connect("toggled", self.on_toggled)

        column = Gtk.TreeViewColumn(_("monitor"), renderer, active=2, visible=3)
        self.tview.append_column(column)
     
        window.show()
    
    def on_toggled(self, renderer, path):
        path = Gtk.TreePath(path)
        v = not self.tstore[path][2]
        self.tstore[path][2] = v
        
        self.le.set_property("count-visible", v)
        
        for dat in self.data:
            if path == self.tstore.get_path(dat.iter): # comparing iters directly does not work
                self.monitor = dat.id() if v else self.MONITOR_NONE
            else:
                self.tstore[dat.iter][2] = False

    def initialize_gui(self):
        for dat in self.data:
            t = dat.type()
            monitor = dat.id() == self.monitor
            dat.read()
            dat.iter = self.tstore.append(self.group[t], [dat.label(), dat.str_val(), monitor, t in self.MONITOR_TYPES])
        
        for t, i in enumerate(self.DISPLAY_TYPES):  
            if self.expanded[i]:
                self.tview.expand_row(self.tstore.get_path(self.group[t]), False)
        
    def refresh_gui(self):           
        for dat in self.data:
            dat.read()
            
            # display value in icon
            if dat.id() == self.monitor:
                self.le.set_property("count", dat.val)
            
            self.tstore[dat.iter][1] = dat.str_val()
        
        return True # to be called again
    
    def initialize(self):
        for chip in sensors.ChipIterator():
            for feature in sensors.FeatureIterator(chip):
                if feature.type not in self.DISPLAY_TYPES:
                    continue
            
                self.data.append(Sensor((chip, feature)))

        self.initialize_gui()
    
    def run(self):
        if os.path.exists(self.SENSORS_CONF):
            sensors.init(self.SENSORS_CONF)
        elif "SNAP" in os.environ:
            sensors.init(os.environ["SNAP"]+"/etc/sensors3.conf")
        else:
            sensors.init()
        
        self.initialize()
        GObject.timeout_add_seconds(1, self.refresh_gui)
        Gtk.main()
    
    def end(self, *a):
        expanded = [self.tview.row_expanded(self.tstore.get_path(self.group[t])) for t in self.DISPLAY_TYPES]
        monitor = [e.decode("utf-8") for e in self.monitor]
        
        config_dir = GLib.get_user_config_dir()

        if not os.path.exists(config_dir):
            # need this for SNAPs
            os.mkdir(config_dir)

        json.dump({"expanded": expanded, "monitor": monitor}, open(self.CONFIG_FILE, "w"))

        sensors.cleanup()
        Gtk.main_quit()
        
if __name__ == '__main__':
    c = Controller()
    c.run()
