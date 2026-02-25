#!/usr/bin/env python3

# Wave Interference Galaxy - inspired by Dusty’s galaxy engines

# Multiple traveling wave sources create interference patterns

# Each wave has its own color, speed, and decay

import sys, time, math, random as R

# Config

FPS = 30
WIDTH = 80
GLYPH = “█”
WAVE_COUNT = 4
SPAWN_RATE = 0.08  # probability per frame

# Wave parameters

SPEED_RANGE = (0.3, 1.2)
DECAY_RANGE = (0.92, 0.98)
AMPLITUDE_RANGE = (0.6, 1.0)

def clamp(x, lo=0, hi=255):
return max(lo, min(hi, int(x)))

def paint_fg(r, g, b):
return f”\x1b[38;2;{r};{g};{b}m”

def hsv_to_rgb(h, s, v):
“”“h in [0,1], s in [0,1], v in [0,1]”””
if s == 0:
return (int(255*v), int(255*v), int(255*v))
i = int(h * 6.0)
f = (h * 6.0) - i
p = v * (1.0 - s)
q = v * (1.0 - s * f)
t = v * (1.0 - s * (1.0 - f))
i = i % 6
if i == 0: rgb = (v, t, p)
elif i == 1: rgb = (q, v, p)
elif i == 2: rgb = (p, v, t)
elif i == 3: rgb = (p, q, v)
elif i == 4: rgb = (t, p, v)
else: rgb = (v, p, q)
return tuple(int(255 * c) for c in rgb)

class Wave:
def **init**(self):
self.pos = R.random() * WIDTH
self.speed = R.uniform(*SPEED_RANGE)
self.decay = R.uniform(*DECAY_RANGE)
self.amplitude = R.uniform(*AMPLITUDE_RANGE)
self.hue = R.random()
self.phase = R.random() * 2 * math.pi
self.alive = True

```
def update(self):
    self.pos += self.speed
    self.amplitude *= self.decay
    if self.amplitude < 0.01 or self.pos > WIDTH + 20:
        self.alive = False
        
def value_at(self, x, t):
    """Wave function: dampened traveling sine"""
    if not self.alive:
        return 0
    dist = abs(x - self.pos)
    # Exponential falloff with distance
    envelope = math.exp(-dist / 15.0)
    # Traveling wave with phase
    wave_val = math.sin((x - self.pos) * 0.3 + self.phase + t * 0.1)
    return self.amplitude * envelope * wave_val
```

def main():
waves = []
t = 0

```
sys.stdout.write("\x1b[?25l")  # hide cursor
try:
    while True:
        # Spawn new waves
        if R.random() < SPAWN_RATE:
            waves.append(Wave())
        
        # Update all waves
        for w in waves:
            w.update()
        waves = [w for w in waves if w.alive]
        
        # Keep at least 2 waves alive
        while len(waves) < 2:
            waves.append(Wave())
        
        # Calculate interference at each position
        row = []
        for x in range(WIDTH):
            # Sum all wave contributions
            total = 0
            color_r, color_g, color_b = 0, 0, 0
            weight_sum = 0
            
            for w in waves:
                val = w.value_at(x, t)
                total += val
                
                # Weight color by absolute wave contribution
                weight = abs(val) * w.amplitude
                r, g, b = hsv_to_rgb(w.hue, 0.8, 0.9)
                color_r += r * weight
                color_g += g * weight
                color_b += b * weight
                weight_sum += weight
            
            # Normalize colors
            if weight_sum > 0.01:
                color_r = clamp(color_r / weight_sum)
                color_g = clamp(color_g / weight_sum)
                color_b = clamp(color_b / weight_sum)
                
                # Brightness based on interference magnitude
                brightness = min(1.0, abs(total) / len(waves))
                color_r = clamp(color_r * brightness)
                color_g = clamp(color_g * brightness)
                color_b = clamp(color_b * brightness)
            else:
                color_r = color_g = color_b = 0
            
            row.append((color_r, color_g, color_b))
        
        # Render row
        out = []
        for r, g, b in row:
            out.append(paint_fg(r, g, b) + GLYPH)
        out.append("\x1b[0m\n")
        sys.stdout.write("".join(out))
        sys.stdout.flush()
        
        t += 1
        time.sleep(1.0 / FPS)
        
except KeyboardInterrupt:
    pass
finally:
    sys.stdout.write("\x1b[0m\x1b[?25h")  # reset, show cursor
```

if **name** == “**main**”:
main()