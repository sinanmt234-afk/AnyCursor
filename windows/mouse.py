import ctypes, ctypes.wintypes
u = ctypes.windll.user32
try: u.SetProcessDPIAware()
except Exception: pass
_rx = _ry = 0.0
def pos():
    p = ctypes.wintypes.POINT(); u.GetCursorPos(ctypes.byref(p)); return p.x, p.y
def screen(): return u.GetSystemMetrics(0), u.GetSystemMetrics(1)
def move_to(x, y):
    w, h = screen(); u.SetCursorPos(int(max(0, min(w-1, x))), int(max(0, min(h-1, y))))
def move_by(dx, dy):
    global _rx, _ry
    _rx += dx; _ry += dy
    ix, iy = int(_rx), int(_ry); _rx -= ix; _ry -= iy
    if ix or iy: u.mouse_event(0x0001, ix, iy, 0, 0)
_B = {"left": (0x2, 0x4), "right": (0x8, 0x10)}
def down(b="left"): u.mouse_event(_B[b][0], 0, 0, 0, 0)
def up(b="left"): u.mouse_event(_B[b][1], 0, 0, 0, 0)
def click(b="left"): down(b); up(b)
def dbl(): click(); click()
def wheel(n): u.mouse_event(0x0800, 0, 0, int(n), 0)
def key(vk, release=False): u.keybd_event(vk, 0, 2 if release else 0, 0)
def hotkey(*vks):
    for v in vks: key(v)
    for v in reversed(vks): key(v, True)
def ctrl_wheel(n): key(0x11); wheel(n); key(0x11, True)
def key_down(vk): return u.GetAsyncKeyState(vk) & 0x8000
