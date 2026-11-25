import cv2, math, time, threading
import mediapipe as mp
import mouse

LE = [33, 160, 158, 133, 153, 144]
RE = [362, 385, 387, 263, 373, 380]
d = lambda a, b: math.hypot(a.x - b.x, a.y - b.y)
def ear(lm, ids):
    p = [lm[i] for i in ids]
    return (d(p[1], p[5]) + d(p[2], p[4])) / (2 * d(p[0], p[3]))

class Tracker(threading.Thread):
    def __init__(s):
        super().__init__(daemon=True)
        s.mode, s.prev, s.alive, s.sens = "head", "head", True, 1.0
        s.neutral, s.recal, s.status = None, False, "Starting camera…"
        s.cs, s.blinks, s.lastb = None, 0, 0.0
        s.mouth_n, s.mouth_lock = 0, False
        s.sm, s.pinch, s.rlock, s.hk = None, False, False, False

    def run(s):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW); cap.set(3, 640); cap.set(4, 480)
        face = mp.solutions.face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True,
                                               min_detection_confidence=.5, min_tracking_confidence=.5)
        hands = mp.solutions.hands.Hands(max_num_hands=1, model_complexity=0,
                                         min_detection_confidence=.6, min_tracking_confidence=.5)
        while s.alive:
            hot = mouse.key_down(0x11) and mouse.key_down(0x12) and mouse.key_down(0x50)  # Ctrl+Alt+P
            if hot and not s.hk:
                if s.mode == "off": s.mode = s.prev
                else: s.prev, s.mode = s.mode, "off"
            s.hk = bool(hot)
            ok, f = cap.read()
            if not ok: s.status = "Camera not available"; time.sleep(.3); continue
            if s.mode == "off":
                s.status = "Paused"; s.release(); time.sleep(.05); continue
            rgb = cv2.cvtColor(cv2.flip(f, 1), cv2.COLOR_BGR2RGB)
            if s.mode == "head": s.head(face.process(rgb))
            else: s.hand(hands.process(rgb))
        cap.release()

    def release(s):
        if s.pinch: mouse.up(); s.pinch = False

    def head(s, r):
        s.release()
        if not r.multi_face_landmarks: s.status = "No face found"; return
        lm = r.multi_face_landmarks[0].landmark
        n = lm[1]
        if s.neutral is None or s.recal: s.neutral, s.recal = (n.x, n.y), False
        now = time.time()
        e = (ear(lm, LE) + ear(lm, RE)) / 2
        mar = d(lm[13], lm[14]) / d(lm[78], lm[308])
        mouth_open = mar > .45
        closed = e < .19 and not mouth_open
        if not closed:
            def v(o):
                dz = .012
                return 0 if abs(o) < dz else (abs(o) - dz) * math.copysign(1, o)
            mouse.move_by(v(n.x - s.neutral[0]) * 420 * s.sens, v(n.y - s.neutral[1]) * 520 * s.sens)
        if closed:
            if s.cs is None: s.cs = now
        elif s.cs is not None:
            if .04 < now - s.cs < .5: s.blinks += 1; s.lastb = now
            s.cs = None
        if s.blinks and s.cs is None and now - s.lastb > .45:
            mouse.dbl() if s.blinks >= 2 else mouse.click()
            s.status = "Double click" if s.blinks >= 2 else "Click"; s.blinks = 0
        if mouth_open:
            s.mouth_n += 1
            if s.mouth_n >= 4 and not s.mouth_lock:
                mouse.click("right"); s.mouth_lock = True; s.status = "Right click"
        else: s.mouth_n, s.mouth_lock = 0, False
        if not (s.blinks or s.mouth_lock): s.status = "Head tracking active"

    def hand(s, r):
        if not r.multi_hand_landmarks:
            s.status = "No hand found"; s.release(); return
        lm = r.multi_hand_landmarks[0].landmark
        x = min(1, max(0, (lm[8].x - .15) / .7)); y = min(1, max(0, (lm[8].y - .15) / .7))
        W, H = mouse.screen(); tx, ty = x * W, y * H
        s.sm = (tx, ty) if s.sm is None else (s.sm[0] + (tx - s.sm[0]) * .35, s.sm[1] + (ty - s.sm[1]) * .35)
        mouse.move_to(*s.sm)
        size = d(lm[0], lm[9])
        p = d(lm[4], lm[8]) / size < .28
        if p and not s.pinch: mouse.down(); s.pinch = True
        elif not p and s.pinch: mouse.up(); s.pinch = False
        rp = d(lm[4], lm[12]) / size < .28
        if rp and not s.rlock: mouse.click("right"); s.rlock = True
        elif not rp: s.rlock = False
        s.status = "Hand tracking: pinch = click / drag"
