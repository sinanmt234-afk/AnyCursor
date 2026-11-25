import asyncio, json, random, threading
import websockets
import mouse

SWIPE = {"up": (0x5B, 0x09), "down": (0x5B, 0x44), "left": (0x11, 0x5B, 0x25), "right": (0x11, 0x5B, 0x27)}

def handle(m):
    t = m.get("t")
    if t == "move": mouse.move_by(m["dx"] * 1.8, m["dy"] * 1.8)
    elif t == "click": mouse.click()
    elif t == "right": mouse.click("right")
    elif t == "down": mouse.down()
    elif t == "up": mouse.up()
    elif t == "scroll": mouse.wheel(m["dy"] * 8)
    elif t == "zoom": mouse.ctrl_wheel(120 * m["d"])
    elif t == "swipe": mouse.hotkey(*SWIPE[m["d"]])

class Server(threading.Thread):
    port = 8765
    def __init__(s):
        super().__init__(daemon=True)
        s.pin = f"{random.randint(0, 999999):06d}"; s.clients = 0

    async def h(s, ws):
        try:
            m = json.loads(await asyncio.wait_for(ws.recv(), 10))
            if m.get("pin") != s.pin: await ws.send('{"ok":false}'); return
            await ws.send('{"ok":true}'); s.clients += 1
            try:
                async for raw in ws: handle(json.loads(raw))
            finally: s.clients -= 1
        except Exception: pass

    async def main(s):
        async with websockets.serve(s.h, "0.0.0.0", s.port): await asyncio.Future()

    def run(s): asyncio.run(s.main())
