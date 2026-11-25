"""Screenshots and screen recordings on Linux desktops through D-Bus.

Wayland does not let ordinary programs read the screen. Screenshots go through the
xdg-desktop-portal (the route apps are meant to use) and recordings through GNOME Shell's
built-in screen recorder, which keeps recording only while the connection that started it
stays open.
"""

import logging
import shutil
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from hi_puter.core.errors import ActionError

log = logging.getLogger("hi_puter")

PORTAL = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SCREENCAST = "org.gnome.Shell.Screencast"
SCREENCAST_PATH = "/org/gnome/Shell/Screencast"
MAX_RECORDING_SECONDS = 60 * 60  # stop a forgotten recording after an hour


def screenshots_folder() -> Path:
    return Path.home() / "Pictures" / "Screenshots"


def recordings_folder() -> Path:
    return Path.home() / "Videos" / "Screencasts"


def _jeepney() -> Any:
    try:
        import jeepney
        import jeepney.io.blocking
    except ImportError as exc:
        raise ActionError("Screen capture needs the jeepney package: pip install jeepney") from exc
    return jeepney


def _open_session() -> Any:
    jeepney = _jeepney()
    try:
        return jeepney.io.blocking.open_dbus_connection(bus="SESSION")
    except Exception as exc:  # no session bus (e.g. over SSH)
        raise ActionError("No desktop session to capture.") from exc


def _keep(path: Path) -> Path:
    """Move a capture into ~/Pictures/Screenshots with a readable name."""
    folder = screenshots_folder()
    folder.mkdir(parents=True, exist_ok=True)
    if path.parent == folder:
        return path
    target = folder / f"Screenshot {datetime.now():%Y-%m-%d %H-%M-%S}{path.suffix or '.png'}"
    shutil.move(str(path), target)
    return target


def portal_screenshot(interactive: bool, timeout: float = 120) -> Path | None:
    """Ask the desktop portal for a screenshot.

    Returns the saved file, or None if the user cancelled or the portal refused (a silent
    capture needs a one-time permission that some desktops only grant to known apps).
    """
    jeepney = _jeepney()
    connection = _open_session()
    try:
        token = "hiputer" + uuid.uuid4().hex[:8]
        sender = connection.unique_name[1:].replace(".", "_")
        handle = f"{PORTAL_PATH}/request/{sender}/{token}"
        rule = jeepney.MatchRule(
            type="signal",
            interface="org.freedesktop.portal.Request",
            member="Response",
            path=handle,
        )
        jeepney.io.blocking.Proxy(jeepney.message_bus, connection).AddMatch(rule)
        portal = jeepney.DBusAddress(
            PORTAL_PATH, bus_name=PORTAL, interface="org.freedesktop.portal.Screenshot"
        )
        options = {"handle_token": ("s", token), "interactive": ("b", interactive)}
        with connection.filter(rule) as queue:
            reply = connection.send_and_get_reply(
                jeepney.new_method_call(portal, "Screenshot", "sa{sv}", ("", options))
            )
            if reply.header.message_type.name == "error":
                raise ActionError("The screenshot service isn't available on this desktop.")
            signal = connection.recv_until_filtered(queue, timeout=timeout)
        code, results = signal.body
        if code != 0:
            log.info("Portal screenshot not taken (response %s)", code)
            return None
        path = Path(unquote(urlparse(results.get("uri", ("s", ""))[1]).path))
        return _keep(path) if path.is_file() else None
    except TimeoutError:
        return None
    finally:
        connection.close()


def open_screenshot_tool() -> None:
    """Open the desktop's screenshot tool and save whatever the user captures, in the background."""

    def wait_for_capture() -> None:
        try:
            path = portal_screenshot(interactive=True, timeout=600)
            log.info("Screenshot %s", f"saved to {path}" if path else "cancelled")
        except ActionError as exc:
            log.warning("Screenshot tool failed: %s", exc)

    threading.Thread(target=wait_for_capture, daemon=True).start()


class ScreenRecorder:
    """GNOME Shell's built-in recorder, held open by one D-Bus connection."""

    def __init__(self) -> None:
        self._connection: Any = None
        self._path: Path | None = None
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    @property
    def recording(self) -> bool:
        return self._connection is not None

    def start(self, seconds: float | None = None) -> Path:
        jeepney = _jeepney()
        with self._lock:
            if self._connection is not None and self._path is not None:
                return self._path
            folder = recordings_folder()
            folder.mkdir(parents=True, exist_ok=True)
            connection = _open_session()
            shell = jeepney.DBusAddress(SCREENCAST_PATH, bus_name=SCREENCAST, interface=SCREENCAST)
            template = str(folder / "Screencast from %d %t.webm")
            reply = connection.send_and_get_reply(
                jeepney.new_method_call(
                    shell, "Screencast", "sa{sv}", (template, {"draw-cursor": ("b", True)})
                )
            )
            started = reply.header.message_type.name != "error" and bool(reply.body[0])
            if not started:
                connection.close()
                raise ActionError("The screen recorder couldn't start on this desktop.")
            self._connection = connection
            self._path = Path(reply.body[1])
            limit = min(seconds, MAX_RECORDING_SECONDS) if seconds else MAX_RECORDING_SECONDS
            self._timer = threading.Timer(limit, self.stop)
            self._timer.daemon = True
            self._timer.start()
            return self._path

    def stop(self) -> Path | None:
        jeepney = _jeepney()
        with self._lock:
            if self._connection is None:
                return None
            if self._timer is not None:
                self._timer.cancel()
            shell = jeepney.DBusAddress(SCREENCAST_PATH, bus_name=SCREENCAST, interface=SCREENCAST)
            try:
                self._connection.send_and_get_reply(
                    jeepney.new_method_call(shell, "StopScreencast")
                )
            finally:
                # Closing the connection also ends the recording if the call failed.
                self._connection.close()
                self._connection = None
            path, self._path = self._path, None
            return path
