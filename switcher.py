import obspython as obs
from Xlib import display as xdisplay
from screeninfo import get_monitors

CURSOR_CHECK_INTERVAL_MS = 100

active_display = None
d = xdisplay.Display()
root = d.screen().root


def log(msg):
    obs.script_log(obs.LOG_INFO, f"[cursor-switcher] {msg}")


def script_description():
    return """
Multi-Monitor Cursor Tracking for OBS Studio Linux / i3

Tracks mouse position and shows only the OBS scene item named:
Display 1, Display 2, Display 3, ...

Important:
Use scene sources/items named exactly Display 1, Display 2, etc.
"""


def script_load(settings):
    log_monitors()
    obs.timer_remove(check_cursor_position)
    obs.timer_add(check_cursor_position, CURSOR_CHECK_INTERVAL_MS)


def script_update(settings):
    obs.timer_remove(check_cursor_position)
    obs.timer_add(check_cursor_position, CURSOR_CHECK_INTERVAL_MS)


def script_unload():
    obs.timer_remove(check_cursor_position)


def log_monitors():
    monitors = get_monitors()
    for i, m in enumerate(monitors):
        log(f"Display {i + 1}: x={m.x}, y={m.y}, w={m.width}, h={m.height}")


def get_cursor_position():
    data = root.query_pointer()._data
    return data["root_x"], data["root_y"]


def get_display_from_pos(x, y):
    monitors = get_monitors()

    for i, m in enumerate(monitors):
        if m.x <= x < m.x + m.width and m.y <= y < m.y + m.height:
            return f"Display {i + 1}"

    return None


def check_cursor_position():
    global active_display

    x, y = get_cursor_position()
    current_display = get_display_from_pos(x, y)

    if current_display is None:
        return

    if current_display != active_display:
        toggle_display_sources(current_display)


def toggle_display_sources(current_display):
    global active_display

    scene_source = obs.obs_frontend_get_current_scene()
    if scene_source is None:
        return

    scene = obs.obs_scene_from_source(scene_source)
    if scene is None:
        obs.obs_source_release(scene_source)
        return

    scene_items = obs.obs_scene_enum_items(scene)
    if scene_items is None:
        obs.obs_source_release(scene_source)
        return

    items = []

    for item in scene_items:
        source = obs.obs_sceneitem_get_source(item)
        if source:
            name = obs.obs_source_get_name(source)

            if name.startswith("Display "):
                items.append((item, name))

    names = [name for _, name in items]

    if current_display not in names:
        log(f"Could not find scene item named {current_display}. Found: {names}")
        obs.sceneitem_list_release(scene_items)
        obs.obs_source_release(scene_source)
        return

    for item, name in items:
        visible = name == current_display
        obs.obs_sceneitem_set_visible(item, visible)

    active_display = current_display
    log(f"Switched to {current_display}")

    obs.sceneitem_list_release(scene_items)
    obs.obs_source_release(scene_source)


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_button(
        props,
        "refresh",
        "Print Monitor Mapping",
        refresh_display_sources
    )
    return props


def refresh_display_sources(props, prop):
    log_monitors()
    active_display = None
    return True
