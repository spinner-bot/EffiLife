#!/usr/bin/env python3
"""Capture a native X11 display rectangle through GDK, without GPU access."""
from pathlib import Path
import ctypes
import sys

def main():
    if len(sys.argv) not in {2, 6}:
        raise SystemExit("Usage: capture-display.py output.png [x y width height]")
    pointer = ctypes.c_void_p
    gdk = ctypes.CDLL("libgdk-3.so.0")
    pixbuf = ctypes.CDLL("libgdk_pixbuf-2.0.so.0")
    objects = ctypes.CDLL("libgobject-2.0.so.0")
    gdk.gdk_init.argtypes = [pointer, pointer]
    gdk.gdk_get_default_root_window.restype = pointer
    gdk.gdk_window_get_width.argtypes = [pointer]
    gdk.gdk_window_get_height.argtypes = [pointer]
    gdk.gdk_pixbuf_get_from_window.argtypes = [pointer, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    gdk.gdk_pixbuf_get_from_window.restype = pointer
    pixbuf.gdk_pixbuf_savev.argtypes = [pointer, ctypes.c_char_p, ctypes.c_char_p, pointer, pointer, pointer]
    objects.g_object_unref.argtypes = [pointer]
    gdk.gdk_init(None, None)
    window = gdk.gdk_get_default_root_window()
    if not window:
        raise SystemExit("No native display is available")
    dimensions = list(map(int, sys.argv[2:])) if len(sys.argv) == 6 else [0, 0, gdk.gdk_window_get_width(window), gdk.gdk_window_get_height(window)]
    image = gdk.gdk_pixbuf_get_from_window(window, *dimensions)
    if not image:
        raise SystemExit("Native display capture failed")
    destination = Path(sys.argv[1])
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = pixbuf.gdk_pixbuf_savev(image, str(destination).encode(), b"png", None, None, None)
    objects.g_object_unref(image)
    if not result:
        raise SystemExit("Could not write the native display capture")

if __name__ == "__main__":
    main()

