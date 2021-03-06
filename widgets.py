import glob
import os
from gi.repository import Gtk, GdkPixbuf
import gi

gi.require_version("Gtk", "3.0")


class ProgramBox(Gtk.VBox):
    def __init__(self, program_name, option, check_programs):
        Gtk.Box.__init__(self)
        self.program_name = program_name
        self.check_programs = check_programs
        self.get_func_by_opt(option)

    def new_toggle_button(self):
        btn = Gtk.ToggleButton("Install")
        btn.set_name(self.program_name)
        return btn

    def new_choose_button(self):
        btn = Gtk.Button("Choose")
        btn.set_name(self.program_name)
        return btn

    def image(self):
        icon_path = glob.glob(
            os.path.dirname(os.path.abspath(__file__))
            + "/icons/"
            + self.program_name
            + ".*"
        )[0]
        if not icon_path:
            img = Gtk.Image()
            img.set_opacity(0)
            return img

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=icon_path, width=72, height=72, preserve_aspect_ratio=True
        )
        img = Gtk.Image.new_from_pixbuf(pixbuf)
        return img

    def toggle_install(self):
        label = Gtk.Label(self.program_name)
        self.button = self.new_toggle_button()
        if self.program_name in self.check_programs:
            self.button.set_active(True)
            self.button.set_sensitive(False)
            self.pack_end(self.button, False, False, 0)
        else:
            self.pack_end(self.button, False, False, 0)
        self.pack_start(self.image(), False, False, 0)
        self.pack_start(label, False, False, 0)

    def choose_install(self):
        label = Gtk.Label(self.program_name)
        self.button = self.new_choose_button()
        self.pack_start(self.image(), False, False, 0)
        self.pack_start(label, False, False, 0)
        self.pack_end(self.button, False, False, 0)

    def get_func_by_opt(self, option):
        options = {
            "click_install": self.toggle_install,
            "show_releases": self.choose_install,
        }
        options.get(option)()


class FlowBox(Gtk.FlowBox):
    """
    FlowBox element which is used for program boxes
    """

    def __init__(self, objects):
        Gtk.FlowBox.__init__(self)
        self.set_homogeneous(False)
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.set_min_children_per_line(0)
        self.set_max_children_per_line(3)

        self.add_programs(objects)

    def add_programs(self, objects):
        if objects[0]:
            for _program in objects[0]:
                _box = ProgramBox(_program, "click_install", objects[4])
                self.add(_box)
                objects[0][_program] = _box.button
                _box.button.connect("clicked", objects[2].toggl_nec_programs)

        if objects[1]:
            for _program in objects[1]:
                _box = ProgramBox(_program, "show_releases", objects[4])
                btn_obj = _box.button
                objects[1][_program][1] = btn_obj
                self.add(_box)
                btn_obj.connect("clicked", objects[2].choose_release)
                # create the version selector window
                api_link = objects[1][_program][0]
                selector, tree_store = objects[3](api_link, _program)
                objects[1][_program][2] = selector
                objects[1][_program][3] = tree_store


class MessageDialog(Gtk.Dialog):
    """
    Used to make message window to warn the user
    """

    def __init__(self, parent, title, message):
        Gtk.Dialog.__init__(
            self, title, parent, 0, (Gtk.STOCK_OK, Gtk.ResponseType.OK,),
        )
        label = Gtk.Label(message)
        label.set_line_wrap_mode(Gtk.WrapMode.CHAR)
        box = self.get_content_area()
        box.add(label)
        self.set_default_size(120, 100)
        self.show()


class ReleaseSelector(Gtk.ApplicationWindow):
    """
    Window to install different version of the program.
    Currently used only for proton-ge.
    """

    def __init__(self, program_name, json_objects, check_programs):
        Gtk.Window.__init__(self)
        self.set_deletable(False)
        self.program_name = program_name
        self.json_objects = json_objects
        self.hide_on_delete()
        self.set_default_size(250, 300)
        if check_programs[program_name]:
            self.tree_view = TreeView(self.json_objects, check_programs[program_name])
        else:
            self.tree_view = TreeView(self.json_objects, False)

        self.add(self.body())

    def body(self):
        def top_label():
            label = Gtk.Label()
            text = self.program_name + " version managment."
            label.set_text(text)
            label.set_margin_bottom(10)
            return label

        def scroll_tree_view():
            scrolled_win = Gtk.ScrolledWindow()
            scrolled_win.add(self.tree_view)
            return scrolled_win

        def bottom_button():
            button = Gtk.Button("Hide")
            button.connect("clicked", self.on_hide)
            button.set_halign(Gtk.Align.END)
            button.set_margin_top(5)
            return button

        box = Gtk.VBox()
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_right(10)
        box.set_margin_left(10)
        box.pack_start(top_label(), False, True, 0)
        box.pack_start(scroll_tree_view(), True, True, 0)
        box.pack_end(bottom_button(), False, False, 0)
        return box

    def on_hide(self, args):
        self.hide()


class TreeView(Gtk.TreeView):
    def __init__(self, json_objects, installed):
        Gtk.TreeView.__init__(self)
        self.data_objects = json_objects

        # if release of this program is already installed
        self.installed = installed
        self.store = self.list_store()
        self.set_model(self.store)
        self.set_columns_renderers()

    def set_columns_renderers(self):
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn("", renderer_toggle, active=0)
        self.append_column(column_toggle)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Release", renderer_text, text=1)
        self.append_column(column_text)

        renderer_release_type = Gtk.CellRendererText()
        column_release_type = Gtk.TreeViewColumn(
            "Prelease ?", renderer_release_type, text=2
        )
        self.append_column(column_release_type)

    def list_store(self):
        _list_store = Gtk.ListStore(bool, str, str)

        if self.installed:
            for data_object in self.data_objects:
                check_button = Gtk.CheckButton()
                tag_name = data_object.get("tag_name")
                check_button.set_name(tag_name)
                release = data_object.get("prerelease")
                if tag_name in self.installed:
                    pass
                else:
                    _list_store.append([False, str(tag_name), str(release)])
            return _list_store

        for data_object in self.data_objects:
            check_button = Gtk.CheckButton()
            tag_name = data_object.get("tag_name")
            check_button.set_name(tag_name)
            release = data_object.get("prerelease")
            _list_store.append([False, str(tag_name), str(release)])
        return _list_store

    def on_cell_toggled(self, widget, path):
        self.store[path][0] = not self.store[path][0]
