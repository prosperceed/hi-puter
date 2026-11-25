"""Media control on Linux through MPRIS, the D-Bus interface Spotify, VLC and browsers expose."""

import re
import shutil
import subprocess

from hi_puter.core.errors import ActionError

PREFIX = "org.mpris.MediaPlayer2."
OBJECT = "/org/mpris/MediaPlayer2"
METHODS = {
    "play": "Play",
    "pause": "Pause",
    "toggle": "PlayPause",
    "next": "Next",
    "previous": "Previous",
}
SANDBOX_HINT = (
    "{app} blocked the request. Start Hi-Puter from a normal terminal: apps installed as snaps "
    "only accept media controls from regular programs."
)


def _gdbus(*args: str) -> str:
    binary = shutil.which("gdbus")
    if binary is None:
        raise ActionError("Media control needs gdbus (part of GLib), which isn't installed.")
    result = subprocess.run(
        [binary, "call", "--session", *args], capture_output=True, text=True, timeout=5, check=False
    )
    if result.returncode != 0:
        raise ActionError(result.stderr.strip() or "D-Bus call failed")
    return result.stdout


def players() -> list[str]:
    """Bus names of running media players, e.g. org.mpris.MediaPlayer2.spotify."""
    listing = _gdbus(
        "--dest", "org.freedesktop.DBus", "--object-path", "/org/freedesktop/DBus",
        "--method", "org.freedesktop.DBus.ListNames",
    )  # fmt: skip
    return re.findall(rf"'({re.escape(PREFIX)}[^']+)'", listing)


def _label(bus_name: str) -> str:
    """org.mpris.MediaPlayer2.spotify -> Spotify; ...firefox.instance_1_23 -> Firefox."""
    return bus_name.removeprefix(PREFIX).split(".")[0].replace("_", " ").title()


def _is_playing(bus_name: str) -> bool:
    try:
        status = _gdbus(
            "--dest", bus_name, "--object-path", OBJECT,
            "--method", "org.freedesktop.DBus.Properties.Get",
            "org.mpris.MediaPlayer2.Player", "PlaybackStatus",
        )  # fmt: skip
    except ActionError:
        return False
    return "Playing" in status


def choose_player(available: list[str], app: str | None, playing: list[str]) -> str | None:
    """The player for `app` if named, otherwise the one playing now, otherwise the only one."""
    if app:
        words = [w for w in re.findall(r"[a-z0-9]+", app.lower()) if w not in {"the", "app"}]
        for bus_name in available:
            short = bus_name.removeprefix(PREFIX).lower()
            if any(word in short for word in words):
                return bus_name
        return None
    if playing:
        return playing[0]
    return available[0] if len(available) == 1 else None


def control(action: str, app: str | None = None) -> str:
    """Send play/pause/next/previous; returns the player's display name."""
    method = METHODS.get(action)
    if method is None:
        raise ActionError(f"Unknown media action {action}.")
    available = players()
    if not available:
        raise ActionError("No music or video app is open.")
    playing = [] if app else [name for name in available if _is_playing(name)]
    target = choose_player(available, app, playing)
    if target is None:
        if app:
            raise ActionError(f"{app.title()} isn't open or doesn't support media controls.")
        names = ", ".join(_label(name) for name in available)
        raise ActionError(f"Which app? I can control {names}.")
    try:
        _gdbus(
            "--dest", target, "--object-path", OBJECT,
            "--method", f"org.mpris.MediaPlayer2.Player.{method}",
        )  # fmt: skip
    except ActionError as exc:
        if "AccessDenied" in str(exc) or "AppArmor" in str(exc):
            raise ActionError(SANDBOX_HINT.format(app=_label(target))) from exc
        raise
    return _label(target)
