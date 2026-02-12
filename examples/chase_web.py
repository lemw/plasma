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
from machine import Pin, PWM

NUM_LEDS = 60
TRAIL_LENGTH = 4  # number of fading trail LEDs behind each head

# --- Global state (modified by web requests) ---
speed = 25        # 0 (stop) to 100 (fast)
color_r = 255     # current chase colour
color_g = 0
color_b = 0
remember = False  # paint mode: LEDs keep their colour

# Colour sequence for button cycling
COLOR_SEQUENCE = [
    (255,   0,   0),  # red
    (255, 136,   0),  # orange
    (255, 255,   0),  # yellow
    (0,   255,   0),  # green
    (0,   255, 255),  # cyan
    (0,     0, 255),  # blue
    (136,   0, 255),  # purple
    (255,   0, 255),  # magenta
    (255,  20, 147),  # pink
    (255, 255, 255),  # white
]
color_index = 0

# Button A on GPIO 12 (active low)
button_a = Pin(12, Pin.IN, Pin.PULL_UP)

# Store painted colour for each LED (used in paint mode)
painted = [(0, 0, 0)] * NUM_LEDS

# --- LED strip setup ---
led_strip = plasma.WS2812(NUM_LEDS, color_order=plasma.COLOR_ORDER_BGR)
led_strip.start()

# Onboard RGB LED via PWM (active-low: duty 65535=off, 0=full on)
# ~15% intensity to keep it subtle
ONBOARD_DIM = 0.15
onboard_r = PWM(Pin(16), freq=1000, duty_u16=65535)
onboard_g = PWM(Pin(17), freq=1000, duty_u16=65535)
onboard_b = PWM(Pin(18), freq=1000, duty_u16=65535)


def update_onboard_led():
    """Set onboard LED to current chase colour at reduced intensity."""
    # Active-low: duty = 65535 means off, 0 means full on
    onboard_r.duty_u16(65535 - int(color_r * ONBOARD_DIM * 257))
    onboard_g.duty_u16(65535 - int(color_g * ONBOARD_DIM * 257))
    onboard_b.duty_u16(65535 - int(color_b * ONBOARD_DIM * 257))


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
    """Single chaser with fading trail. In paint mode, LEDs keep their colour."""
    global speed, color_r, color_g, color_b, remember, painted
    offset = 0
    DIM = 0.4  # painted LEDs shown at 40% so the chaser head is visible

    while True:
        head = offset % NUM_LEDS

        if remember:
            # Paint mode: stamp current colour onto this LED
            painted[head] = (color_r, color_g, color_b)

            # Show all painted LEDs at reduced brightness
            for i in range(NUM_LEDS):
                pr, pg, pb = painted[i]
                led_strip.set_rgb(i, int(pr * DIM), int(pg * DIM), int(pb * DIM))

            # Chaser head at full brightness
            led_strip.set_rgb(head, color_r, color_g, color_b)

            # Fading trail
            for t in range(1, TRAIL_LENGTH + 1):
                trail_idx = (head - t) % NUM_LEDS
                fade = 1.0 - (t / (TRAIL_LENGTH + 1))
                pr, pg, pb = painted[trail_idx]
                # Trail blends from full chase colour down to painted colour
                tr = max(int(pr * DIM), int(color_r * fade * fade))
                tg = max(int(pg * DIM), int(color_g * fade * fade))
                tb = max(int(pb * DIM), int(color_b * fade * fade))
                led_strip.set_rgb(trail_idx, tr, tg, tb)
        else:
            # Normal mode: clear all, show chaser only
            for i in range(NUM_LEDS):
                led_strip.set_rgb(i, 0, 0, 0)

            led_strip.set_rgb(head, color_r, color_g, color_b)

            for t in range(1, TRAIL_LENGTH + 1):
                trail_idx = (head - t) % NUM_LEDS
                fade = 1.0 - (t / (TRAIL_LENGTH + 1))
                tr = int(color_r * fade * fade)
                tg = int(color_g * fade * fade)
                tb = int(color_b * fade * fade)
                led_strip.set_rgb(trail_idx, tr, tg, tb)

        # Update onboard LED to match current colour
        update_onboard_led()

        # Speed 0 = paused, 1-100 maps ~200ms down to ~10ms
        if speed == 0:
            await uasyncio.sleep(0.1)
            continue

        offset = (offset + 1) % NUM_LEDS
        delay = max(0.01, 0.21 - (speed * 0.002))
        await uasyncio.sleep(delay)


# ---------------------------------------------------------------------------
# Button A handler (async)
# ---------------------------------------------------------------------------
async def button_loop():
    """Poll button A: short=next colour, double=stop, long=toggle paint."""
    global color_r, color_g, color_b, color_index, remember, painted, speed
    LONG_PRESS_MS = 600
    DOUBLE_PRESS_MS = 300

    while True:
        if button_a.value() == 0:  # pressed (active low)
            press_start = time.ticks_ms()
            long_fired = False

            # Wait for release, but fire long press while held
            while button_a.value() == 0:
                duration = time.ticks_diff(time.ticks_ms(), press_start)
                if not long_fired and duration >= LONG_PRESS_MS:
                    remember = not remember
                    if not remember:
                        painted = [(0, 0, 0)] * NUM_LEDS
                    print(f"[BTN] Paint mode: {'ON' if remember else 'OFF'}")
                    long_fired = True
                await uasyncio.sleep_ms(20)

            if not long_fired:
                # Short press — wait to see if a second press follows
                second_press = False
                wait_start = time.ticks_ms()
                while time.ticks_diff(time.ticks_ms(), wait_start) < DOUBLE_PRESS_MS:
                    if button_a.value() == 0:
                        second_press = True
                        # Wait for second release
                        while button_a.value() == 0:
                            await uasyncio.sleep_ms(20)
                        break
                    await uasyncio.sleep_ms(20)

                if second_press:
                    # Double press: toggle stop/resume
                    speed = 0 if speed > 0 else 25
                    print(f"[BTN] Speed: {speed}")
                else:
                    # Single press: next colour
                    color_index = (color_index + 1) % len(COLOR_SEQUENCE)
                    color_r, color_g, color_b = COLOR_SEQUENCE[color_index]
                    print(f"[BTN] Colour: ({color_r},{color_g},{color_b})")

        await uasyncio.sleep_ms(50)


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
  <input type="range" id="speed" min="0" max="100" value="{speed}">
  <div class="val" id="sval">{speed}</div>

  <label style="display:flex;align-items:center;gap:.6em;margin-top:1.2em;cursor:pointer">
    <input type="checkbox" id="remember" {"checked" if remember else ""}  style="width:22px;height:22px;accent-color:#e94560">
    <span>Remember (paint mode)</span>
  </label>
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
  document.getElementById('remember').addEventListener('change', e => {{
    send('remember=' + (e.target.checked ? '1' : '0'));
  }});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Parse query string from HTTP request
# ---------------------------------------------------------------------------
def parse_request(raw):
    """Extract query parameters from a raw HTTP request."""
    global speed, color_r, color_g, color_b, remember, painted

    try:
        line = raw.split(b"\r\n")[0].decode()
        if "?" not in line:
            return
        query = line.split("?")[1].split(" ")[0]
        for param in query.split("&"):
            key, val = param.split("=")
            if key == "speed":
                speed = max(0, min(100, int(val)))
            elif key == "color":
                hex_str = val.strip("#")
                color_r = int(hex_str[0:2], 16)
                color_g = int(hex_str[2:4], 16)
                color_b = int(hex_str[4:6], 16)
            elif key == "remember":
                remember = val == "1"
                if not remember:
                    # Clear the painted canvas
                    painted = [(0, 0, 0)] * NUM_LEDS
        # Auto-save removed — remember now means paint mode
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
        button_loop(),
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
