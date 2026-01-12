import obspython as obs
import time
from Xlib import display as xdisplay
from screeninfo import get_monitors

CURSOR_CHECK_INTERVAL_MS = 100
active_display = None
display_sources = {}

d = xdisplay.Display()
root = d.screen().root
monitors = get_monitors()


def script_description():
    return """Multi-Monitor Cursor Tracking for OBS Studio (Linux / i3)

Tracks mouse position and switches OBS Display Capture sources named:
Display 1, Display 2, ... according to active monitor.
"""


def script_update(settings):
    obs.timer_remove(check_cursor_position)
    obs.timer_add(check_cursor_position, CURSOR_CHECK_INTERVAL_MS)


def script_unload():
    obs.timer_remove(check_cursor_position)


def get_cursor_position():
    data = root.query_pointer()._data
    return data["root_x"], data["root_y"]


def get_display_from_pos(x, y):
    for i, m in enumerate(monitors):
        if m.x <= x < m.x + m.width and m.y <= y < m.y + m.height:
            return f"Display {i+1}"
    return None


def check_cursor_position():
    global active_display

    x, y = get_cursor_position()
    current_display = get_display_from_pos(x, y)

    if current_display != active_display:
        toggle_display_sources(current_display)


def toggle_display_sources(current_display):
    global active_display

    for display, source in display_sources.items():
        enabled = (display == current_display)
        obs.obs_source_set_enabled(source, enabled)

    active_display = current_display


def script_load(settings):
    global display_sources
    display_sources.clear()

    scene = obs.obs_frontend_get_current_scene()
    if scene is None:
        return

    scene_source = obs.obs_scene_from_source(scene)
    if scene_source is None:
        obs.obs_source_release(scene)
        return

    scene_items = obs.obs_scene_enum_items(scene_source)

    for item in scene_items:
        source = obs.obs_sceneitem_get_source(item)
        if source:
            name = obs.obs_source_get_name(source)
            if name.startswith("Display "):
                display_sources[name] = source

    obs.sceneitem_list_release(scene_items)
    obs.obs_source_release(scene)


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_button(props, "refresh", "Refresh Display Sources", refresh_display_sources)
    return props


def refresh_display_sources(props, prop):
    script_load(None)
    return True
