"""
LED Chase Animation with WiFi Web Control
for Pimoroni Plasma 2350W + WS2812 LED strip.

A single LED chases around the strip with a fading trail.
Speed and colour are controllable from a web browser.

Upload this file + secrets.py to the board and run it.
"""

import time
import plasma
import network
import socket
import uasyncio

NUM_LEDS = 60
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

    # Always start fresh — stale state after soft reboot can look "connected"
    wlan.disconnect()
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)

    # Disable WiFi power saving — fixes CYW43 ioctl timeouts
    wlan.config(pm=0xa11140)

    print(f"Connecting to {WIFI_SSID}...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    max_wait = 30
    while max_wait > 0:
        status = wlan.status()
        if status == 3:
            break
        if status < 0:
            print(f"WiFi failed with status: {status}")
            break
        print(f"  waiting... (status={status})")
        time.sleep(1)
        max_wait -= 1

    if status != 3:
        raise RuntimeError(f"WiFi connection failed (status={status})")

    time.sleep(2)

    ip = wlan.ifconfig()[0]
    print(f"Connected! IP: {ip}")
    print(f"Open http://{ip} in your browser")
    return ip


# ---------------------------------------------------------------------------
# Chase animation (async)
# ---------------------------------------------------------------------------
async def chase_loop():
    """Single chaser with fading trail."""
    global speed, color_r, color_g, color_b
    offset = 0

    while True:
        # Clear all LEDs
        for i in range(NUM_LEDS):
            led_strip.set_rgb(i, 0, 0, 0)

        head = offset % NUM_LEDS
        led_strip.set_rgb(head, color_r, color_g, color_b)

        for t in range(1, TRAIL_LENGTH + 1):
            trail_idx = (head - t) % NUM_LEDS
            fade = 1.0 - (t / (TRAIL_LENGTH + 1))
            tr = int(color_r * fade * fade)
            tg = int(color_g * fade * fade)
            tb = int(color_b * fade * fade)
            led_strip.set_rgb(trail_idx, tr, tg, tb)

        offset = (offset + 1) % NUM_LEDS

        delay = max(0.01, 0.21 - (speed * 0.002))
        await uasyncio.sleep(delay)


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
# Web server (async, non-blocking)
# ---------------------------------------------------------------------------
async def web_server():
    """Async HTTP server on port 80 using uasyncio stream API."""

    async def handle_client(reader, writer):
        peer = writer.get_extra_info("peername")
        print(f"[WEB] Client connected from {peer}")
        try:
            request = await reader.read(1024)
            req_line = request.split(b"\r\n")[0].decode() if request else "(empty)"
            print(f"[WEB] Request: {req_line}")
            parse_request(request)
            response = build_page()
            writer.write(response)
            await writer.drain()
            print(f"[WEB] Response sent ({len(response)} bytes)")
        except Exception as e:
            print(f"[WEB] Client error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"[WEB] Connection closed")

    server = await uasyncio.start_server(handle_client, "0.0.0.0", 80)
    print("[WEB] Web server listening on port 80")

    # Verify WiFi is still up
    wlan = network.WLAN(network.STA_IF)
    print(f"[WEB] WiFi connected: {wlan.isconnected()}")
    print(f"[WEB] IP config: {wlan.ifconfig()}")

    while True:
        # Periodic WiFi health check
        if not wlan.isconnected():
            print("[WEB] WARNING: WiFi disconnected!")
        await uasyncio.sleep(10)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    await uasyncio.gather(
        chase_loop(),
        web_server(),
    )


ip = wifi_connect()
try:
    uasyncio.run(main())
except KeyboardInterrupt:
    pass
finally:
    for i in range(NUM_LEDS):
        led_strip.set_rgb(i, 0, 0, 0)
    print("Bye!")
