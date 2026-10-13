"""Capture the README screenshots from the running app (Playwright, Chromium).

    .venv/bin/python tools/screenshots/capture.py                 # app at http://localhost:5173
    .venv/bin/python tools/screenshots/capture.py --base http://localhost:7860 --only twin-overview,fleet

Needs the backend and the frontend running (or the container), and once:
    .venv/bin/pip install -r tools/screenshots/requirements.txt && .venv/bin/python -m playwright install chromium

Every image is a real page of the running app. The script never edits the page: it only navigates, clicks, types in
search and waits for the data to settle. It stops with an error if the dev-only FAKE BOARD banner is showing, so a
rehearsal with tools/fake_board.py can't end up in the README. Output: docs/screenshots/<name>.png, plus
forklift-route.mp4 when ffmpeg is installed (the raw Playwright .webm otherwise).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, sync_playwright
from websockets.sync.client import connect

OUT = Path(__file__).resolve().parents[2] / "docs" / "screenshots"
DESKTOP = {"width": 1440, "height": 900}
PHONE = {"width": 390, "height": 844}
# Long enough for the WebSocket snapshot, the first unit updates, the device registry and the 3D scene's first frames.
SETTLE_S = 5.0
# Goto targets tried for the route clip, spread over the warehouse and the factory.
ROUTE_TARGETS = ["ZONE_A", "RACK_B4", "CHARGER_C2", "FAC_OUT", "RAW_BAY_1", "FAC_AISLE_2"]


def clear_selection(base: str) -> None:
    """Selection is shared by every screen (server state), so one shot's selected forklift would open its card in the
    next. Send the same intent a click on empty ground sends."""
    with connect(base.replace("http", "ws", 1) + "/ws", open_timeout=10) as ws:
        ws.send(json.dumps({"type": "select_unit", "unit_id": None, "cmd_id": f"readme-shots-{time.time_ns()}"}))
        time.sleep(0.5)


def send_fl01_on_route(base: str) -> str:
    """For the route clip: ask the server to drive FL-01 somewhere, the same move_unit intent an operator sends from
    /control (the unit becomes source "manual"). Dry-run a few goto targets and send the one with the longest planned
    path, so the clip shows a whole route. Returns the target, or "" if the server refused all of them."""
    best: tuple[int, str] = (0, "")
    with connect(base.replace("http", "ws", 1) + "/ws", open_timeout=10) as ws:
        def ask(target: str, dry: bool) -> dict:  # type: ignore[type-arg]
            cmd_id = f"readme-mv-{time.time_ns()}"
            ws.send(json.dumps({"type": "move_unit", "cmd_id": cmd_id, "unit_id": "FL-01", "target_node": target,
                                "action": "goto", "dry_run": dry}))
            while True:
                m = json.loads(ws.recv(timeout=10))
                if m.get("type") == "command_ack" and m.get("cmd_id") == cmd_id:
                    return m
        for target in ROUTE_TARGETS:
            ack = ask(target, True)
            if ack.get("ok") and len(ack.get("path") or []) > best[0]:
                best = (len(ack["path"]), target)
        if best[1] and ask(best[1], False).get("ok"):
            return best[1]
    return ""


def wait_live(page: Page) -> None:
    """Pages with the top bar show a green "Live" pill once the WebSocket is up; others just get the settle time."""
    try:
        page.get_by_role("status").filter(has_text="Live").first.wait_for(timeout=15_000)
    except Exception:
        pass
    time.sleep(SETTLE_S)


def search(page: Page, text: str) -> None:
    # Below 1800 px the search folds into an icon; "/" opens and focuses it at every width.
    page.keyboard.press("/")
    time.sleep(0.4)
    page.keyboard.type(text, delay=40)
    time.sleep(0.8)
    page.keyboard.press("Enter")
    time.sleep(0.4)
    page.keyboard.press("Escape")  # clears and closes the search box; the selection stays


def select_fl01(page: Page) -> None:
    search(page, "FL-01")
    time.sleep(3)


def factory_view(page: Page) -> None:
    search(page, "FAC-01")
    time.sleep(4)


def gateway_card(page: Page) -> None:
    search(page, "GW-01")
    time.sleep(3)


def fleet_attention(page: Page) -> None:
    btn = page.get_by_role("button", name="Needs attention").first
    if btn.count():
        btn.click()
        time.sleep(1)


@dataclass
class Shot:
    name: str
    path: str
    viewport: dict[str, int]
    action: Callable[[Page], None] | None = None
    note: str = ""


SHOTS = [
    Shot("twin-overview", "/twin", DESKTOP),
    Shot("twin-inspect-forklift", "/twin", DESKTOP, select_fl01),
    Shot("campus-factory", "/twin", DESKTOP, factory_view),
    Shot("twin-gateway-card", "/twin", DESKTOP, gateway_card),
    Shot("control-room", "/control", DESKTOP),
    Shot("control-phone", "/control", PHONE),
    Shot("device-page", "/device", DESKTOP),
    Shot("wiring-breadboard-fl01", "/wiring/fl01_sensor_pack?view=breadboard", DESKTOP),
    Shot("wiring-schematic-fl01", "/wiring/fl01_sensor_pack?view=schematic", DESKTOP),
    Shot("wiring-reference-kit", "/wiring/machine_monitor?view=breadboard", DESKTOP),
    Shot("kits-index", "/kits", DESKTOP),
    Shot("fleet", "/fleet", DESKTOP, fleet_attention),
    Shot("monitor", "/monitor", DESKTOP),
    Shot("rules", "/rules", DESKTOP),
    Shot("energy", "/energy", DESKTOP),
    Shot("model", "/model", DESKTOP),
]


def fake_banner_showing(page: Page) -> bool:
    return page.get_by_text("FAKE BOARD", exact=False).count() > 0


def capture(base: str, only: set[str] | None, video: bool) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failed = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for shot in SHOTS:
            if only and shot.name not in only:
                continue
            clear_selection(base)
            phone = shot.viewport is PHONE
            ctx = browser.new_context(viewport=shot.viewport, device_scale_factor=2 if phone else 1,
                                      is_mobile=phone, has_touch=phone)
            page = ctx.new_page()
            try:
                page.goto(base + shot.path, wait_until="domcontentloaded")
                wait_live(page)
                if fake_banner_showing(page):
                    sys.exit("FAKE BOARD banner is showing: stop tools/fake_board.py and clear its retained hello first.")
                if shot.action:
                    shot.action(page)
                    time.sleep(1)
                page.screenshot(path=str(OUT / f"{shot.name}.png"))
                print(f"ok   {shot.name}.png")
            except Exception as e:  # keep going so one broken page doesn't hide the others
                failed += 1
                print(f"FAIL {shot.name}: {e}")
            finally:
                ctx.close()
        if video and (not only or "forklift-route" in only):
            failed += record_route(browser, base)
        browser.close()
    return failed


def record_route(browser, base: str) -> int:  # type: ignore[no-untyped-def]
    """About 12 s of /twin with FL-01 selected, driving a route the server planned (see send_fl01_on_route)."""
    tmp = OUT / "_video"
    ctx = browser.new_context(viewport=DESKTOP, record_video_dir=str(tmp), record_video_size=DESKTOP)
    page = ctx.new_page()
    t0 = time.monotonic()  # the video starts with the page
    try:
        page.goto(base + "/twin", wait_until="domcontentloaded")
        wait_live(page)
        select_fl01(page)
        target = send_fl01_on_route(base)
        print(f"     forklift-route: FL-01 -> {target or 'no route accepted (clip shows whatever the server does)'}")
        start_s = time.monotonic() - t0
        time.sleep(12)
    finally:
        ctx.close()
    webm = next(tmp.glob("*.webm"), None)
    if not webm:
        print("FAIL forklift-route: Playwright wrote no video")
        return 1
    if shutil.which("ffmpeg"):
        # Drop page load, settle and search so the clip starts on the selected forklift.
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start_s:.1f}", "-i", str(webm), "-vf", "scale=1200:-2",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
                        str(OUT / "forklift-route.mp4")], check=True)
        print("ok   forklift-route.mp4")
    else:
        shutil.copy(webm, OUT / "forklift-route.webm")
        print("ok   forklift-route.webm (no ffmpeg for mp4)")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://localhost:5173", help="app URL (dev server or container)")
    ap.add_argument("--only", default="", help="comma-separated names, e.g. twin-overview,fleet,forklift-route")
    ap.add_argument("--no-video", action="store_true", help="skip forklift-route")
    a = ap.parse_args()
    only = {s.strip() for s in a.only.split(",") if s.strip()} or None
    sys.exit(1 if capture(a.base.rstrip("/"), only, not a.no_video) else 0)


if __name__ == "__main__":
    main()
