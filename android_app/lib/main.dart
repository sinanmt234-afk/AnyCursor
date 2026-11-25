import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/io.dart';

const bg = Color(0xFF0B0B0F), card = Color(0xFF14141A), silver = Color(0xFFC9CCD6), dim = Color(0xFF7C8196);

void main() => runApp(MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: bg,
        textTheme: GoogleFonts.manropeTextTheme(ThemeData.dark().textTheme).apply(bodyColor: silver, displayColor: silver),
      ),
      home: const Connect(),
    ));

class Connect extends StatefulWidget {
  const Connect({super.key});
  @override
  State<Connect> createState() => _ConnectState();
}

class _ConnectState extends State<Connect> {
  final ip = TextEditingController(), pin = TextEditingController();
  bool busy = false;
  @override
  void initState() {
    super.initState();
    SharedPreferences.getInstance().then((p) => ip.text = p.getString('ip') ?? '');
  }

  Future<void> go() async {
    setState(() => busy = true);
    try {
      final ch = IOWebSocketChannel.connect('ws://${ip.text.trim()}:8765', connectTimeout: const Duration(seconds: 5));
      await ch.ready.timeout(const Duration(seconds: 5));
      ch.sink.add(jsonEncode({'pin': pin.text.trim()}));
      (await SharedPreferences.getInstance()).setString('ip', ip.text.trim());
      if (!mounted) return;
      await Navigator.push(context, MaterialPageRoute(builder: (_) => Pad(ch)));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not connect. Check IP and Wi-Fi.')));
    }
    if (mounted) setState(() => busy = false);
  }

  Widget field(TextEditingController c, String l, TextInputType t) => Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: TextField(
            controller: c,
            keyboardType: t,
            decoration: InputDecoration(
                labelText: l,
                filled: true,
                fillColor: card,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none))),
      );

  @override
  Widget build(BuildContext c) => Scaffold(
        body: SafeArea(
            child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            const Text('ANYTRACK', style: TextStyle(fontSize: 32, fontWeight: FontWeight.w200, letterSpacing: 6)),
            const SizedBox(height: 8),
            const Text('You\'ve got this. Let\'s connect.', style: TextStyle(color: dim)),
            const SizedBox(height: 36),
            field(ip, 'PC IP address (shown in the app)', TextInputType.number),
            field(pin, 'PIN', TextInputType.number),
            SizedBox(
                width: double.infinity,
                height: 54,
                child: FilledButton(
                    style: FilledButton.styleFrom(backgroundColor: const Color(0xFF2A2D3A), foregroundColor: silver),
                    onPressed: busy ? null : go,
                    child: Text(busy ? 'Connecting…' : 'Connect'))),
          ]),
        )),
      );
}

class Pad extends StatefulWidget {
  final IOWebSocketChannel ch;
  const Pad(this.ch, {super.key});
  @override
  State<Pad> createState() => _PadState();
}

class _PadState extends State<Pad> {
  final ptr = <int, Offset>{};
  int maxp = 0;
  double moved = 0, pd = 0;
  DateTime t0 = DateTime.now(), lastTap = DateTime(2000);
  bool drag = false, swiped = false;
  Offset c0 = Offset.zero;

  @override
  void initState() {
    super.initState();
    widget.ch.stream.listen((m) {
      if (m.toString().contains('false') && mounted) Navigator.pop(context);
    }, onDone: () {
      if (mounted) Navigator.pop(context);
    });
  }

  @override
  void dispose() {
    widget.ch.sink.close();
    super.dispose();
  }

  void send(Map m) => widget.ch.sink.add(jsonEncode(m));
  Offset cen() => ptr.values.fold(Offset.zero, (a, b) => a + b) / ptr.length.toDouble();
  double dist2() => (ptr.values.first - ptr.values.last).distance;
  int ms(DateTime a) => DateTime.now().difference(a).inMilliseconds;

  void down(PointerDownEvent e) {
    if (ptr.isEmpty) {
      maxp = 0;
      moved = 0;
      swiped = false;
      t0 = DateTime.now();
      if (ms(lastTap) < 300) {
        drag = true;
        send({'t': 'down'});
      }
    }
    ptr[e.pointer] = e.position;
    maxp = max(maxp, ptr.length);
    if (ptr.length >= 2) pd = dist2();
    c0 = cen();
  }

  void move(PointerMoveEvent e) {
    final old = ptr[e.pointer];
    if (old == null) return;
    ptr[e.pointer] = e.position;
    final d = e.position - old;
    moved += d.distance;
    if (ptr.length == 1 && maxp == 1) {
      send({'t': 'move', 'dx': d.dx, 'dy': d.dy});
    } else if (ptr.length == 2) {
      final nd = dist2();
      if ((nd - pd).abs() > 16) {
        send({'t': 'zoom', 'd': nd > pd ? 1 : -1});
        pd = nd;
      } else {
        send({'t': 'scroll', 'dy': d.dy / 2});
      }
    }
  }

  void up(PointerEvent e) {
    if (maxp >= 3 && !swiped && ptr.length >= 3) {
      final d = cen() - c0;
      if (d.distance > 90) {
        swiped = true;
        send({'t': 'swipe', 'd': d.dx.abs() > d.dy.abs() ? (d.dx > 0 ? 'right' : 'left') : (d.dy > 0 ? 'down' : 'up')});
        HapticFeedback.lightImpact();
      }
    }
    ptr.remove(e.pointer);
    if (ptr.isEmpty) {
      if (drag) {
        send({'t': 'up'});
        drag = false;
        lastTap = DateTime(2000);
      } else if (ms(t0) < 250 && moved < 12) {
        if (maxp == 1) {
          send({'t': 'click'});
          lastTap = DateTime.now();
          HapticFeedback.selectionClick();
        } else if (maxp == 2) {
          send({'t': 'right'});
          HapticFeedback.mediumImpact();
        }
      }
    }
  }

  Widget btn(String l, String t) => Expanded(
        child: GestureDetector(
          onTapDown: (_) {
            send({'t': t == 'right' ? 'right' : 'click'});
            HapticFeedback.selectionClick();
          },
          child: Container(
              height: 76,
              margin: const EdgeInsets.all(6),
              alignment: Alignment.center,
              decoration: BoxDecoration(color: card, borderRadius: BorderRadius.circular(20)),
              child: Text(l, style: const TextStyle(letterSpacing: 3, fontWeight: FontWeight.w300))),
        ),
      );

  @override
  Widget build(BuildContext c) => Scaffold(
        body: SafeArea(
            child: Column(children: [
          Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 8, 0),
              child: Row(children: [
                const Text('Connected  ·  stay positive', style: TextStyle(color: dim)),
                const Spacer(),
                IconButton(icon: const Icon(Icons.close, color: dim), onPressed: () => Navigator.pop(context))
              ])),
          Expanded(
              child: Listener(
                  onPointerDown: down,
                  onPointerMove: move,
                  onPointerUp: up,
                  onPointerCancel: up,
                  child: Container(
                    margin: const EdgeInsets.all(14),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(28),
                        gradient: const LinearGradient(colors: [Color(0xFF16161D), Color(0xFF0F0F14)], begin: Alignment.topLeft, end: Alignment.bottomRight),
                        border: Border.all(color: const Color(0xFF23242E))),
                    child: const Text('glide · tap · double-tap-drag\ntwo-finger scroll / pinch / tap\nthree-finger swipe',
                        textAlign: TextAlign.center, style: TextStyle(color: Color(0xFF3C3F4D), height: 1.9)),
                  ))),
          Row(children: [btn('LEFT', 'left'), btn('RIGHT', 'right')]),
        ])),
      );
}
