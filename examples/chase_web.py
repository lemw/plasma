"""
LED Chase Animation with WiFi Web Control
for Pimoroni Plasma 2350W + 50 LED WS2812 strip.

A single LED chases around the strip with a fading trail.
Speed and colour are controllable from a web browser.
LED animation runs on core 1, web server on core 0 (main thread).

Upload this file + secrets.py to the board and run it.
"""

import time
import plasma
import network
import socket
import _thread

NUM_LEDS = 50
TRAIL_LENGTH = 4  # number of fading trail LEDs behind each head

# --- Global state (modified by web requests) ---
speed = 50        # 1 (slow) to 100 (fast)
color_r = 255     # current chase colour
color_g = 0
color_b = 0

# --- LED strip setup ---
led_strip = plasma.WS2812(NUM_LEDS, color_order=plasma.COLOR_ORDER_BGR)
led_strip.start()


# ---------------------------------------------------------------------------
# WiFi
# ---------------------------------------------------------------------------
def wifi_connect():
    """Connect to WiFi using credentials from secrets.py and return IP."""
    from secrets import WIFI_SSID, WIFI_PASSWORD

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # If already connected (e.g. after soft reboot), skip
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Already connected! Open http://{ip} in your browser")
        return ip

    print(f"Connecting to {WIFI_SSID}...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait = 30
    while max_wait > 0:
        status = wlan.status()
        if wlan.isconnected():
            break
        if status in (-1, -2, -3):
            print(f"WiFi failed with status: {status}")
            break
        print(f"  waiting... (status={status})")
        time.sleep(1)
        max_wait -= 1

    if not wlan.isconnected():
        raise RuntimeError(f"WiFi connection failed (status={wlan.status()})")

    ip = wlan.ifconfig()[0]
    print(f"Connected! Open http://{ip} in your browser")
    return ip


# ---------------------------------------------------------------------------
# Chase animation (runs on second core via _thread)
# ---------------------------------------------------------------------------
def chase_loop():
    """Single chaser with fading trail — runs forever on core 1."""
    global speed, color_r, color_g, color_b
    offset = 0

    while True:
        # Clear all LEDs
        for i in range(NUM_LEDS):
            led_strip.set_rgb(i, 0, 0, 0)

        head = offset % NUM_LEDS

        # Head LED at full brightness
        led_strip.set_rgb(head, color_r, color_g, color_b)

        # Fading trail behind the head
        for t in range(1, TRAIL_LENGTH + 1):
            trail_idx = (head - t) % NUM_LEDS
            fade = 1.0 - (t / (TRAIL_LENGTH + 1))
            tr = int(color_r * fade * fade)
            tg = int(color_g * fade * fade)
            tb = int(color_b * fade * fade)
            led_strip.set_rgb(trail_idx, tr, tg, tb)

        offset = (offset + 1) % NUM_LEDS

        # Speed maps 1-100 → ~200ms down to ~10ms delay
        delay = max(0.01, 0.21 - (speed * 0.002))
        time.sleep(delay)


# ---------------------------------------------------------------------------
# Web page HTML
# ---------------------------------------------------------------------------
def build_page():
    """Return the control page HTML."""
    hex_color = "#{:02x}{:02x}{:02x}".format(color_r, color_g, color_b)
    return f"""\
HTTP/1.0 200 OK\r
Content-Type: text/html\r
Connection: close\r
\r
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plasma Chase</title>
<style>
  body {{
    font-family: -apple-system, sans-serif;
    background: #1a1a2e; color: #eee;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    min-height: 100vh; margin: 0;
  }}
  h1 {{ color: #e94560; }}
  .card {{
    background: #16213e; border-radius: 16px;
    padding: 2em; margin: 1em; width: min(90vw, 360px);
    box-shadow: 0 4px 24px rgba(0,0,0,.4);
  }}
  label {{ display: block; margin: 1em 0 .3em; font-size: 1.1em; }}
  input[type=color] {{
    width: 100%; height: 60px; border: none;
    border-radius: 8px; cursor: pointer;
  }}
  input[type=range] {{
    width: 100%; accent-color: #e94560;
  }}
  .val {{ text-align: center; font-size: 1.4em; margin-top: .3em; }}
  .swatches {{
    display: grid; grid-template-columns: repeat(6, 1fr);
    gap: 8px; margin-top: 1em;
  }}
  .sw {{
    aspect-ratio: 1; border-radius: 8px; border: 2px solid #0002;
    cursor: pointer; transition: transform .1s;
  }}
  .sw:active {{ transform: scale(0.9); }}
</style>
</head>
<body>
<h1>&#x2728; Plasma Chase</h1>
<div class="card">
  <label>Quick Colours</label>
  <div class="swatches">
    <div class="sw" style="background:#ff0000" onclick="c('ff0000')"></div>
    <div class="sw" style="background:#ff8800" onclick="c('ff8800')"></div>
    <div class="sw" style="background:#ffff00" onclick="c('ffff00')"></div>
    <div class="sw" style="background:#00ff00" onclick="c('00ff00')"></div>
    <div class="sw" style="background:#00ffff" onclick="c('00ffff')"></div>
    <div class="sw" style="background:#0000ff" onclick="c('0000ff')"></div>
    <div class="sw" style="background:#8800ff" onclick="c('8800ff')"></div>
    <div class="sw" style="background:#ff00ff" onclick="c('ff00ff')"></div>
    <div class="sw" style="background:#ff1493" onclick="c('ff1493')"></div>
    <div class="sw" style="background:#ffffff" onclick="c('ffffff')"></div>
    <div class="sw" style="background:#ffaa55" onclick="c('ffaa55')"></div>
    <div class="sw" style="background:#88ff00" onclick="c('88ff00')"></div>
  </div>

  <label for="color">Custom Colour</label>
  <input type="color" id="color" value="{hex_color}">

  <label for="speed">Speed</label>
  <input type="range" id="speed" min="1" max="100" value="{speed}">
  <div class="val" id="sval">{speed}</div>
</div>

<script>
  function send(p) {{ fetch('/?'+p).catch(()=>{{}}); }}
  function c(hex) {{
    send('color='+hex);
    document.getElementById('color').value='#'+hex;
  }}
  document.getElementById('color').addEventListener('input', e => {{
    c(e.target.value.substring(1));
  }});
  const slider = document.getElementById('speed');
  const sval   = document.getElementById('sval');
  slider.addEventListener('input', e => {{
    sval.textContent = e.target.value;
    send('speed=' + e.target.value);
  }});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Parse query string from HTTP request
# ---------------------------------------------------------------------------
def parse_request(raw):
    """Extract query parameters from a raw HTTP request."""
    global speed, color_r, color_g, color_b

    try:
        line = raw.split(b"\r\n")[0].decode()
        if "?" not in line:
            return
        query = line.split("?")[1].split(" ")[0]
        for param in query.split("&"):
            key, val = param.split("=")
            if key == "speed":
                speed = max(1, min(100, int(val)))
            elif key == "color":
                hex_str = val.strip("#")
                color_r = int(hex_str[0:2], 16)
                color_g = int(hex_str[2:4], 16)
                color_b = int(hex_str[4:6], 16)
    except Exception as e:
        print("Parse error:", e)


# ---------------------------------------------------------------------------
# Web server (runs on main thread / core 0)
# ---------------------------------------------------------------------------
def web_server():
    """Blocking HTTP server on port 80."""
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(2)

    print("Web server listening on port 80")

    while True:
        try:
            cl, remote = s.accept()
            cl.settimeout(2)
            request = cl.recv(1024)
            parse_request(request)
            cl.send(build_page())
        except Exception as e:
            print("Client error:", e)
        finally:
            try:
                cl.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
ip = wifi_connect()

# Start LED animation on the second core
_thread.start_new_thread(chase_loop, ())

# Run web server on main thread (keeps REPL responsive to Ctrl+C)
try:
    web_server()
except KeyboardInterrupt:
    pass
finally:
    for i in range(NUM_LEDS):
        led_strip.set_rgb(i, 0, 0, 0)
    print("Bye!")
