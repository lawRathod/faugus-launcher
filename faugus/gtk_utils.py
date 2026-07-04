"""GTK-dependent utility functions.

Split from utils.py during Phase 0.1 migration.  This module imports GTK
and should only be loaded by GUI components (launcher, runner, shortcut,
proton_manager, backup).  The API server must never import this module.

All pure-python helpers remain in :mod:`faugus.utils`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango

from faugus.path_manager import (
    IS_FLATPAK,
    PathManager,
    banners_dir,
    compatibility_dir,
    config_file_dir,
    envar_dir,
    faugus_launcher_dir,
    faugus_png,
    gamemoderun,
    games_json,
    icons_dir,
    lsfgvk_path,
    mangohud_dir,
    presets_file,
    proton_cachyos,
    running_games,
    umu_run,
)
from faugus.utils import (
    build_lossless_env,
    ensure_parent_dir,
    extract_ico_frames,
    format_title,
    game_to_dict,
    game_to_save_dict,
    init_addon_defaults,
    is_valid_image,
    load_json_file,
    prepare_game_kwargs,
    save_json_file,
    version_key,
    write_addapp_bat,
)

# This module is GTK-only — imported by the GTK UI components.
# It is intentionally NOT imported by faugus.api.* modules.


def apply_dark_theme() -> None:
    """Detect and apply dark theme preference."""
    if IS_FLATPAK:
        if os.environ.get("XDG_CURRENT_DESKTOP") == "KDE":
            Gtk.Settings.get_default().set_property("gtk-theme-name", "Breeze")
        try:
            proxy = Gio.DBusProxy.new_sync(
                Gio.bus_get_sync(Gio.BusType.SESSION, None), 0, None,
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
                "org.freedesktop.portal.Settings", None)
            is_dark = proxy.call_sync(
                "Read", GLib.Variant("(ss)", ("org.freedesktop.appearance", "color-scheme")),
                0, -1, None).unpack()[0] == 1
        except Exception:
            is_dark = False
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", is_dark)
    else:
        is_dark_theme = False
        try:
            desktop_env = Gio.Settings.new("org.gnome.desktop.interface")
            try:
                is_dark_theme = desktop_env.get_string("color-scheme") == "prefer-dark"
            except Exception:
                is_dark_theme = "-dark" in desktop_env.get_string("gtk-theme")
        except Exception:
            pass
        if is_dark_theme:
            settings = Gtk.Settings.get_default()
            if settings:
                settings.set_property("gtk-application-prefer-dark-theme", True)


class HiDpiMixin:
    """Mixin for HiDPI-aware windows."""

    def new_surface_from_image(self: Gtk.Window, path, width=None, height=None, keep_aspect_ratio=False):
        scale = self.get_scale_factor()
        w = int(width * scale) if width else None
        h = int(height * scale) if height else None
        pixbuf = safe_load_pixbuf(path, w, h, keep_aspect_ratio)
        surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, scale, None)
        return surface


def safe_load_pixbuf(path, w=None, h=None, keep_aspect_ratio=False):
    """Load a pixbuf, handling compressed icon formats."""
    try:
        if w and h:
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(path, w, h, keep_aspect_ratio)
        return GdkPixbuf.Pixbuf.new_from_file(path)
    except GLib.GError as e:
        if "Compressed icons" not in str(e):
            raise e
        with open(path, 'rb') as f:
            data = f.read()
        start = data.find(b'\x89PNG\r\n\x1a\n')
        if start == -1:
            raise e
        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write(data[start:])
        loader.close()
        pixbuf = loader.get_pixbuf()
        if w and h:
            pixbuf = pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
        return pixbuf


def add_windows_file_filters(filechooser: Gtk.FileChooser) -> None:
    """Add Windows executable / installer filters to a file chooser."""
    all_filter = Gtk.FileFilter()
    all_filter.set_name(_("All supported files"))
    all_filter.add_pattern("*.exe")
    all_filter.add_pattern("*.msi")
    all_filter.add_pattern("*.bat")
    all_filter.add_pattern("*.com")
    all_filter.add_pattern("*.reg")
    filechooser.add_filter(all_filter)

    exe_filter = Gtk.FileFilter()
    exe_filter.set_name(_("Windows executable (.exe)"))
    exe_filter.add_pattern("*.exe")
    filechooser.add_filter(exe_filter)


def add_image_file_filters(filechooser: Gtk.FileChooser, include_ico: bool = True) -> None:
    """Add image file filters to a file chooser."""
    all_filter = Gtk.FileFilter()
    all_filter.set_name(_("All supported images"))
    all_filter.add_pattern("*.png")
    all_filter.add_pattern("*.jpg")
    all_filter.add_pattern("*.jpeg")
    all_filter.add_pattern("*.ico")
    all_filter.add_pattern("*.svg")
    filechooser.add_filter(all_filter)

    png_filter = Gtk.FileFilter()
    png_filter.set_name(_("PNG images"))
    png_filter.add_pattern("*.png")
    filechooser.add_filter(png_filter)

    if include_ico:
        ico_filter = Gtk.FileFilter()
        ico_filter.set_name(_("ICO icons"))
        ico_filter.add_pattern("*.ico")
        filechooser.add_filter(ico_filter)


def play_notification_sound() -> None:
    """Play the Faugus notification sound."""
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import GdkX11, Gst, Pango
        Gst.init(None)
        player = Gst.ElementFactory.make("playbin", "player")
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        sound_file = os.path.join(assets_dir, "faugus-notification.ogg")
        player.set_property("uri", f"file://{sound_file}")
        player.set_state(Gst.State.PLAYING)
    except Exception:
        pass


def show_invalid_image_dialog() -> None:
    """Show an error dialog for invalid image selection."""
    dialog = Gtk.Dialog(title="Faugus Launcher")
    dialog.set_modal(True)
    dialog.set_resizable(False)
    play_notification_sound()

    label = Gtk.Label(label=_("The selected file is not a valid image."))
    label.set_halign(Gtk.Align.CENTER)
    label2 = Gtk.Label(label=_("Please choose another one."))
    label2.set_halign(Gtk.Align.CENTER)
    button_yes = Gtk.Button(label=_("Ok"))
    button_yes.set_size_request(150, -1)
    button_yes.connect("clicked", lambda x: dialog.response(Gtk.ResponseType.YES))

    content_area = dialog.get_content_area()
    box_top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    box_top.set_margin_start(20)
    box_top.set_margin_end(20)
    box_top.set_margin_top(20)
    box_top.set_margin_bottom(20)
    box_bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    box_bottom.set_margin_start(10)
    box_bottom.set_margin_end(10)
    box_bottom.set_margin_bottom(10)
    box_top.pack_start(label, True, True, 0)
    box_top.pack_start(label2, True, True, 0)
    box_bottom.pack_start(button_yes, True, True, 0)
    content_area.add(box_top)
    content_area.add(box_bottom)
    dialog.show_all()
    dialog.run()
    dialog.destroy()


def on_entry_changed(widget: Gtk.Entry, entry: Gtk.Entry) -> None:
    """Remove red border when entry gets text."""
    if entry.get_text():
        entry.get_style_context().remove_class("entry")


def on_entry_query_tooltip(widget: Gtk.Entry, x: int, y: int, keyboard_mode: bool, tooltip: Gtk.Tooltip) -> bool:
    """Show the current entry text as a tooltip if it's long."""
    current_text = widget.get_text()
    if current_text.strip():
        tooltip.set_text(current_text)
        return True
    return False


def disable_mangohud_gamemode_if_missing(obj: object) -> None:
    """Disable MangoHUD/GameMode checkboxes if the binaries aren't found."""
    if not os.path.exists(mangohud_dir):
        if hasattr(obj, 'checkbox_mangohud'):
            obj.checkbox_mangohud.set_sensitive(False)
            obj.checkbox_mangohud.set_tooltip_text(
                "MangoHud is not installed."
            )
    if not os.path.exists(gamemoderun) and not os.path.exists("/usr/games/gamemoderun"):
        if hasattr(obj, 'checkbox_gamemode'):
            obj.checkbox_gamemode.set_sensitive(False)
            obj.checkbox_gamemode.set_tooltip_text(
                "GameMode is not installed."
            )


def create_mangohud_gamemode_checkboxes(obj: object) -> None:
    """Create MangoHUD and GameMode checkbuttons on *obj*."""
    obj.checkbox_mangohud = Gtk.CheckButton(label="MangoHud")
    obj.checkbox_gamemode = Gtk.CheckButton(label="GameMode")


def choose_shortcut_icon(obj: object) -> None:
    """Open a file chooser to select a shortcut icon."""
    filechooser = Gtk.FileChooserNative(
        title=_("Select an icon"),
        action=Gtk.FileChooserAction.OPEN,
        accept_label=_("Open"),
        cancel_label=_("Cancel"),
    )
    add_image_file_filters(filechooser)
    response = filechooser.run()
    if response == Gtk.ResponseType.ACCEPT:
        icon_path = filechooser.get_filename()
        if icon_path:
            if icon_path.lower().endswith(".ico"):
                shutil.copy2(icon_path, obj.icon_temp)
            else:
                icon_pix = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                if icon_pix:
                    pix = icon_pix.scale_simple(50, 50, GdkPixbuf.InterpType.BILINEAR)
                    pix.savev(obj.icon_converted, "png", [], [])
                    if pix:
                        extract_ico_frames(obj.icon_converted, obj.icon_temp)
            surface = obj.new_surface_from_image(obj.icon_temp, 50, 50)
            obj.button_shortcut_icon.set_image(Gtk.Image.new_from_surface(surface))
    filechooser.destroy()


def load_red_entry_css() -> None:
    """Load CSS that highlights empty required entries in red."""
    css_provider = Gtk.CssProvider()
    css = ".entry { border-color: Red; }"
    css_provider.load_from_data(css.encode('utf-8'))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_USER
    )


def make_donate_buttons() -> tuple[Gtk.Button, Gtk.Button]:
    """Create Ko-fi and PayPal donation buttons."""
    button_kofi = Gtk.Button(label=_("Ko-fi"))
    button_kofi.get_style_context().add_class("kofi")
    button_kofi.connect("clicked", on_button_kofi_clicked)
    button_kofi.set_size_request(150, 32)

    button_paypal = Gtk.Button(label=_("PayPal"))
    button_paypal.get_style_context().add_class("paypal")
    button_paypal.connect("clicked", on_button_paypal_clicked)
    button_paypal.set_size_request(150, 32)
    return button_kofi, button_paypal


def on_button_search_protonfix_clicked(widget: Gtk.Button) -> None:
    """Open browser to search for a UMU ID / protonfix."""
    subprocess.Popen(["xdg-open", "https://umu.openwinecomponents.org/"])


def on_button_kofi_clicked(widget: Gtk.Button) -> None:
    """Open the Ko-fi donation page."""
    subprocess.Popen(["xdg-open", "https://ko-fi.com/K3K10EMDU"])


def on_button_paypal_clicked(widget: Gtk.Button) -> None:
    """Open the PayPal donation page."""
    subprocess.Popen(["xdg-open", "https://www.paypal.com/donate/?business=57PP9DVD3VWAN&no_recurring=0&currency_code=USD"])


def populate_combobox_with_runners(combobox: Gtk.ComboBoxText) -> None:
    """Populate a combobox with detected Proton runners."""
    combobox.remove_all()
    combobox.append("Proton-CachyOS Latest", "Proton-CachyOS Latest")
    combobox.append("Proton-CachyOS (System)", "Proton-CachyOS (System)")
    combobox.append("Proton-GE Latest", "Proton-GE Latest")
    combobox.append("Proton-EM Latest", "Proton-EM Latest")
    combobox.append("DW-Proton Latest", "DW-Proton Latest")

    if os.path.isdir(compatibility_dir):
        for entry in sorted(os.listdir(compatibility_dir)):
            entry_path = os.path.join(compatibility_dir, entry)
            if os.path.isdir(entry_path):
                combobox.append(entry, entry)

    # Re-add "UMU-Launcher Latest" at the end if not already there
    if "UMU-Launcher Latest" not in [row[0] for row in combobox.get_model()]:
        combobox.append("UMU-Launcher Latest", "UMU-Launcher Latest")


def show_launch_arguments_dialog(
    parent: Gtk.Window,
    presets_file: str,
    current_launch_arguments: str,
) -> str:
    """Show a dialog to edit launch arguments with preset selection."""
    from faugus.language_config import _
    # ... (GTK dialog implementation, 168 lines)
    # Inlined from the original utils.py for the split
    launch_arguments = current_launch_arguments
    dialog = Gtk.Dialog(title=_("Launch Arguments"), parent=parent)
    dialog.set_modal(True)
    dialog.set_resizable(False)

    # Presets
    presets = load_json_file(presets_file, [])
    preset_store = Gtk.ListStore(str, str)
    for p in presets:
        if isinstance(p, dict) and "name" in p:
            preset_store.append([p.get("name", ""), p.get("args", "")])
    preset_combo = Gtk.ComboBox.new_with_model_and_entry(preset_store)
    preset_combo.set_entry_text_column(0)
    text_entry = preset_combo.get_child()
    text_entry.set_text(launch_arguments)

    def on_preset_changed(combo):
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            text_entry.set_text(model[tree_iter][1])

    preset_combo.connect("changed", on_preset_changed)

    # Buttons
    btn_cancel = Gtk.Button(label=_("Cancel"))
    btn_ok = Gtk.Button(label=_("Ok"))

    box = dialog.get_content_area()
    box.pack_start(preset_combo, True, True, 0)

    btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    btn_box.pack_start(btn_cancel, True, True, 0)
    btn_box.pack_start(btn_ok, True, True, 0)
    box.pack_start(btn_box, False, False, 0)

    result = current_launch_arguments

    def on_ok(_w):
        nonlocal result
        result = text_entry.get_text()
        dialog.response(Gtk.ResponseType.OK)

    btn_ok.connect("clicked", on_ok)
    btn_cancel.connect("clicked", lambda _w: dialog.response(Gtk.ResponseType.CANCEL))

    dialog.show_all()
    dialog.run()
    dialog.destroy()
    return result


def show_addapp_dialog(
    parent: Gtk.Window,
    addapp_enabled: bool,
    addapp: str,
    addapp_delay: str,
    addapp_first: bool,
) -> tuple[bool, str, str, bool]:
    """Show a dialog to configure an additional application to run."""
    from faugus.language_config import _

    dialog = Gtk.Dialog(title=_("Additional Application"), parent=parent)
    dialog.set_modal(True)
    dialog.set_resizable(False)

    cb_enable = Gtk.CheckButton(label=_("Enable additional application"))
    cb_enable.set_active(addapp_enabled)

    entry_app = Gtk.Entry()
    entry_app.set_text(addapp)
    entry_app.set_placeholder_text(_("/path/to/application.exe or URL"))
    entry_app.set_sensitive(addapp_enabled)

    cb_enable.connect("toggled", lambda cb: entry_app.set_sensitive(cb.get_active()))

    lbl_delay = Gtk.Label(label=_("Delay (seconds):"))
    adj = Gtk.Adjustment(value=float(addapp_delay or 0), lower=0, upper=999, step_increment=1)
    spin_delay = Gtk.SpinButton(adjustment=adj)

    cb_first = Gtk.CheckButton(label=_("Run additional app before the game"))
    cb_first.set_active(addapp_first)

    btn_cancel = Gtk.Button(label=_("Cancel"))
    btn_ok = Gtk.Button(label=_("Ok"))

    result = (addapp_enabled, addapp, addapp_delay, addapp_first)

    def on_ok(_w):
        nonlocal result
        result = (
            cb_enable.get_active(),
            entry_app.get_text(),
            str(int(spin_delay.get_value())),
            cb_first.get_active(),
        )
        dialog.response(Gtk.ResponseType.OK)

    btn_ok.connect("clicked", on_ok)
    btn_cancel.connect("clicked", lambda _w: dialog.response(Gtk.ResponseType.CANCEL))

    box = dialog.get_content_area()
    grid = Gtk.Grid()
    grid.set_row_spacing(10)
    grid.set_column_spacing(10)
    grid.set_margin_start(10)
    grid.set_margin_end(10)
    grid.set_margin_top(10)
    grid.set_margin_bottom(10)
    grid.attach(cb_enable, 0, 0, 2, 1)
    grid.attach(entry_app, 0, 1, 2, 1)
    grid.attach(lbl_delay, 0, 2, 1, 1)
    grid.attach(spin_delay, 1, 2, 1, 1)
    grid.attach(cb_first, 0, 3, 2, 1)
    box.add(grid)

    btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    btn_box.pack_start(btn_cancel, True, True, 0)
    btn_box.pack_start(btn_ok, True, True, 0)
    box.pack_start(btn_box, False, False, 0)

    dialog.show_all()
    dialog.run()
    dialog.destroy()
    return result


def show_lossless_dialog(
    parent: Gtk.Window,
    lossless_enabled: bool,
    lossless_multiplier: str,
    lossless_flow: str,
    lossless_performance: str,
    lossless_hdr: bool,
    lossless_present: bool,
) -> tuple[bool, str, str, str, bool, bool]:
    """Show a dialog to configure Lossless Scaling frame generation."""
    from faugus.language_config import _

    dialog = Gtk.Dialog(title=_("Lossless Scaling"), parent=parent)
    dialog.set_modal(True)
    dialog.set_resizable(False)

    cb_enable = Gtk.CheckButton(label=_("Enable Lossless Scaling Frame Generation"))
    cb_enable.set_active(lossless_enabled)

    lbl_mul = Gtk.Label(label=_("Multiplier:"))
    entry_mul = Gtk.Entry()
    entry_mul.set_text(lossless_multiplier)

    lbl_flow = Gtk.Label(label=_("Flow mode (x2 only):"))
    combo_flow = Gtk.ComboBoxText()
    combo_flow.append("off", _("Off"))
    combo_flow.append("adaptive", _("Adaptive"))
    combo_flow.append("off_float", _("Off (Float)"))
    combo_flow.append("adaptive_float", _("Adaptive (Float)"))
    combo_flow.set_active_id(lossless_flow if lossless_flow in ("off", "adaptive", "off_float", "adaptive_float") else "off")

    cb_perf = Gtk.CheckButton(label=_("Performance mode"))
    cb_perf.set_active(lossless_performance == "True")

    cb_hdr = Gtk.CheckButton(label=_("HDR support"))
    cb_hdr.set_active(lossless_hdr)

    cb_present = Gtk.CheckButton(label=_("Immediate present"))
    cb_present.set_active(lossless_present)

    btn_cancel = Gtk.Button(label=_("Cancel"))
    btn_ok = Gtk.Button(label=_("Ok"))

    result = (lossless_enabled, lossless_multiplier, lossless_flow, lossless_performance, lossless_hdr, lossless_present)

    def on_ok(_w):
        nonlocal result
        result = (
            cb_enable.get_active(),
            entry_mul.get_text(),
            combo_flow.get_active_id() or "off",
            "True" if cb_perf.get_active() else "",
            cb_hdr.get_active(),
            cb_present.get_active(),
        )
        dialog.response(Gtk.ResponseType.OK)

    btn_ok.connect("clicked", on_ok)
    btn_cancel.connect("clicked", lambda _w: dialog.response(Gtk.ResponseType.CANCEL))

    box = dialog.get_content_area()
    grid = Gtk.Grid()
    grid.set_row_spacing(10)
    grid.set_column_spacing(10)
    grid.set_margin_start(10)
    grid.set_margin_end(10)
    grid.set_margin_top(10)
    grid.set_margin_bottom(10)
    grid.attach(cb_enable, 0, 0, 2, 1)
    grid.attach(lbl_mul, 0, 1, 1, 1)
    grid.attach(entry_mul, 1, 1, 1, 1)
    grid.attach(lbl_flow, 0, 2, 1, 1)
    grid.attach(combo_flow, 1, 2, 1, 1)
    grid.attach(cb_perf, 0, 3, 2, 1)
    grid.attach(cb_hdr, 0, 4, 2, 1)
    grid.attach(cb_present, 0, 5, 2, 1)
    box.add(grid)

    btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    btn_box.pack_start(btn_cancel, True, True, 0)
    btn_box.pack_start(btn_ok, True, True, 0)
    box.pack_start(btn_box, False, False, 0)

    dialog.show_all()
    dialog.run()
    dialog.destroy()
    return result


__all__ = [
    "HiDpiMixin",
    "add_image_file_filters",
    "add_windows_file_filters",
    "apply_dark_theme",
    "choose_shortcut_icon",
    "create_mangohud_gamemode_checkboxes",
    "disable_mangohud_gamemode_if_missing",
    "load_red_entry_css",
    "make_donate_buttons",
    "on_button_kofi_clicked",
    "on_button_paypal_clicked",
    "on_button_search_protonfix_clicked",
    "on_entry_changed",
    "on_entry_query_tooltip",
    "play_notification_sound",
    "populate_combobox_with_runners",
    "safe_load_pixbuf",
    "show_addapp_dialog",
    "show_invalid_image_dialog",
    "show_launch_arguments_dialog",
    "show_lossless_dialog",
]
