#!/usr/bin/env python3
# walker_traits_war.py (modified)
#
# Terminal walkers with inheritable traits and competitive gene-flow.
# Modifications:
# - Added fluctuating background color environment: Each grid cell has a slowly changing background color.
#   Walkers gain/lose vigor based on color similarity to background (beneficial if similar, destructive if dissimilar).
# - Territory: Walkers prefer directions towards cells with colors similar to their own.
# - Dynasty establishment: Added a 'family' ID to group similar walkers. Spawning prefers areas with family presence.
# - Adjusted spawn rates for stability: Lower base spawn probs, but boost based on vigor and territory control.
#   Aim for steady population around max_walkers / 2.
import argparse, random, shutil, sys, time, math
from typing import List, Tuple

N,E,S,W = 1,2,4,8
DIRS = (N,E,S,W)
OPP = {N:S, S:N, E:W, W:E}
VEC = {N:(0,-1), S:(0,1), E:(1,0), W:(-1,0)}
TILES = {
    "light": {0:" ", N:"│", S:"│", E:"─", W:"─", N|S:"│", E|W:"─",
              N|E:"└", E|S:"┌", S|W:"┐", W|N:"┘",
              N|E|S:"├", E|S|W:"┬", S|W|N:"┤", W|N|E:"┴", N|E|S|W:"┼"},
    "heavy": {0:" ", N:"┃", S:"┃", E:"━", W:"━", N|S:"┃", E|W:"━",
              N|E:"┗", E|S:"┏", S|W:"┓", W|N:"┛",
              N|E|S:"┣", E|S|W:"┳", S|W|N:"┫", W|N|E:"┻", N|E|S|W:"╋"},
    "double":{0:" ", N:"║", S:"║", E:"═", W:"═", N|S:"║", E|W:"═",
              N|E:"╚", E|S:"╔", S|W:"╗", W|N:"╝",
              N|E|S:"╠", E|S|W:"╦", S|W|N:"╣", W|N|E:"╩", N|E|S|W:"╬"},
}

def clamp(v, lo, hi): 
    return lo if v<lo else hi if v>hi else v

def rgb_fg(r,g,b): return f"\x1b[38;2;{int(r)};{int(g)};{int(b)}m"
def rgb_bg(r,g,b): return f"\x1b[48;2;{int(r)};{int(g)};{int(b)}m"
RESET = "\x1b[0m"

class ChannelStepper:
    def __init__(self, cur: int, steps: int):
        self.cur = int(clamp(cur,0,255))
        self.steps = max(1, steps)
        self.left = 0; self.sgn = 1; self.q = 0; self.r = 0; self.err = 0
        self.target = self.cur
        self.retarget(random.randint(0,255))
    def retarget(self, tgt: int):
        tgt = int(clamp(tgt,0,255))
        d = tgt - self.cur
        self.sgn = 1 if d>=0 else -1
        ad = abs(d)
        self.q, self.r = divmod(ad, self.steps)
        self.err = 0; self.left = self.steps; self.target = tgt
    def step(self)->int:
        if self.left <= 0:
            self.retarget(random.randint(0,255))
        inc = self.q
        self.err += self.r
        if self.err >= self.steps and self.r != 0:
            self.err -= self.steps; inc += 1
        self.cur = int(clamp(self.cur + self.sgn*inc, 0, 255))
        self.left -= 1
        if self.left == 0: self.cur = self.target
        return self.cur

def norm2(vx, vy):
    n = math.hypot(vx, vy)
    if n == 0: return (0.0,0.0)
    return (vx/n, vy/n)

BIAS_VECTORS = [norm2(1,-1), norm2(-1,-1), norm2(-1,1), norm2(1,1)]

def dir_vec(d:int):
    dx,dy = VEC[d]; n = math.hypot(dx,dy); return (dx/n, dy/n)

def weighted_choice(opts, weights):
    total = sum(weights); r = random.random()*total
    acc = 0.0
    for o,w in zip(opts,weights):
        acc += w
        if r <= acc: return o
    return opts[-1]

def color_distance(c1, c2):
    r1,g1,b1 = c1; r2,g2,b2 = c2
    return math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)

class Walker:
    _next_id = 1
    _next_family_id = 1
    __slots__=("id","family_id","x","y","heading","depth","age","alive",
               "R","G","B","dna_R","dna_G","dna_B","dna_samples",
               "bias","bias_strength","spawn_scale","vigor","lifespan","style")
    def __init__(self, x,y, heading, depth, rgb, grad, style, lifespan,
                 bias=None, bias_strength=None, spawn_scale=1.0, vigor=None, family_id=None):
        self.id = Walker._next_id; Walker._next_id += 1
        self.family_id = Walker._next_family_id if family_id is None else family_id
        if family_id is None: Walker._next_family_id += 1
        self.x,self.y,self.heading = x,y,heading
        self.depth=depth; self.age=0; self.alive=True
        self.R=ChannelStepper(rgb[0],grad); self.G=ChannelStepper(rgb[1],grad); self.B=ChannelStepper(rgb[2],grad)
        self.dna_R=[]; self.dna_G=[]; self.dna_B=[]; self.dna_samples=0
        self.bias = list(random.choice(BIAS_VECTORS)) if bias is None else list(bias)
        self.bias_strength = random.uniform(0.1,0.6) if bias_strength is None else float(bias_strength)
        self.spawn_scale = float(spawn_scale)
        self.vigor = random.uniform(0.85,1.15) if vigor is None else float(vigor)
        self.lifespan = lifespan; self.style = style
    def rgb(self): return (self.R.step(), self.G.step(), self.B.step())
    def record_dna(self, r,g,b):
        if self.dna_samples<3:
            self.dna_R.append(r); self.dna_G.append(g); self.dna_B.append(b); self.dna_samples+=1
    def dna_ready(self): return self.dna_samples>=3
    def average_color(self):
        r = sum(self.dna_R) / len(self.dna_R) if self.dna_R else self.R.cur
        g = sum(self.dna_G) / len(self.dna_G) if self.dna_G else self.G.cur
        b = sum(self.dna_B) / len(self.dna_B) if self.dna_B else self.B.cur
        return (r, g, b)

class World:
    def __init__(self, cols, rows, style, wrap, grad, lifetime, smell_ttl, mix, max_walkers):
        self.cols,self.rows = cols,rows
        self.style=style; self.wrap=wrap; self.grad=grad; self.lifespan=lifetime
        self.mix=clamp(mix,0.0,1.0); self.max_walkers=max_walkers
        self.mask=[[0]*cols for _ in range(rows)]
        self.color=[[(220,220,220)]*cols for _ in range(rows)]  # Foreground trail color
        self.bg_color=[[(random.randint(0,255),random.randint(0,255),random.randint(0,255)) for _ in range(cols)] for _ in range(rows)]  # Background colors
        self.bg_steppers=[[[ChannelStepper(self.bg_color[y][x][i], grad*2) for i in range(3)] for x in range(cols)] for y in range(rows)]  # Slower stepping for bg
        self.scent_ttl=[[0]*cols for _ in range(rows)]
        self.scent=[[None]*cols for _ in range(rows)]
        self.family_presence=[[{0: 0} for _ in range(cols)] for _ in range(rows)]  # Track family control per cell (dict of family_id: count)
        self.walkers=[]; self.spawn_base={0:(0.01,128), 1:(0.0025,64), 2:(0.000625,32)}  # Lowered base probs for stability
        self.spawned_steps={}
    def clear(self):
        self.mask=[[0]*self.cols for _ in range(self.rows)]
        self.color=[[(220,220,220)]*self.cols for _ in range(self.rows)]
        self.bg_color=[[(random.randint(0,255),random.randint(0,255),random.randint(0,255)) for _ in range(self.cols)] for _ in range(self.rows)]
        self.bg_steppers=[[[ChannelStepper(self.bg_color[y][x][i], self.grad*2) for i in range(3)] for x in range(self.cols)] for y in range(self.rows)]
        self.scent_ttl=[[0]*self.cols for _ in range(self.rows)]
        self.scent=[[None]*self.cols for _ in range(self.rows)]
        self.family_presence=[[{0: 0} for _ in range(self.cols)] for _ in range(self.rows)]
        self.walkers.clear(); self.spawned_steps.clear()
    def spawn(self, x=None,y=None,depth=0,heading=None,rgb=None,parent=None):
        if len(self.walkers)>=self.max_walkers: return
        if x is None: x=self.cols//2
        if y is None: y=self.rows//2
        if heading is None: heading=random.choice((N,E,S,W))
        if rgb is None: rgb=(random.randint(0,255),random.randint(0,255),random.randint(0,255))
        if parent:
            bx,by=parent.bias
            bx+=random.uniform(-0.25,0.25); by+=random.uniform(-0.25,0.25); bx,by=norm2(bx,by)
            bstr=clamp(parent.bias_strength+random.uniform(-0.05,0.05),0.05,0.85)
            scale=clamp(parent.spawn_scale*(1+random.uniform(-0.1,0.1)),0.25,3.0)
            vigor=clamp(parent.vigor*(1+random.uniform(-0.05,0.05)),0.7,1.3)
            family_id = parent.family_id
        else:
            bx,by=random.choice(BIAS_VECTORS); bstr=random.uniform(0.1,0.6); scale=1.0; vigor=random.uniform(0.85,1.15)
            family_id = None  # Will assign new
        w=Walker(x,y,heading,depth,rgb,self.grad,self.style,self.lifespan,bias=(bx,by),bias_strength=bstr,spawn_scale=scale,vigor=vigor, family_id=family_id)
        self.walkers.append(w); self.spawned_steps[w.id]=0
        # Prefer spawn in family territory if parent
        if parent:
            territory_bonus = self.get_territory_strength(parent.family_id, x, y)
            w.spawn_scale *= (1 + territory_bonus)
    def glyph(self,x,y): return TILES[self.style].get(self.mask[y][x], " ")
    def step_background(self):
        updates = []
        for y in range(self.rows):
            for x in range(self.cols):
                r = self.bg_steppers[y][x][0].step()
                g = self.bg_steppers[y][x][1].step()
                b = self.bg_steppers[y][x][2].step()
                if (r, g, b) != self.bg_color[y][x]:
                    self.bg_color[y][x] = (r, g, b)
                    updates.append((x, y))
        return updates
    def get_territory_strength(self, family_id, x, y):
        pres = self.family_presence[y][x].get(family_id, 0)
        total = sum(self.family_presence[y][x].values())
        return pres / total if total > 0 else 0
    def update_family_presence(self, w, x, y):
        fid = w.family_id
        if fid not in self.family_presence[y][x]:
            self.family_presence[y][x][fid] = 0
        self.family_presence[y][x][fid] += 1
        # Decay others slightly
        for other_fid in list(self.family_presence[y][x]):
            if other_fid != fid:
                self.family_presence[y][x][other_fid] = max(0, self.family_presence[y][x][other_fid] - 0.1)
                if self.family_presence[y][x][other_fid] <= 0:
                    del self.family_presence[y][x][other_fid]
    def choose_dir(self,w):
        opts=[d for d in (N,E,S,W) if d!=OPP[w.heading]]
        bx,by=w.bias; weights=[]
        w_col = w.average_color()
        for d in opts:
            dx,dy=VEC[d]; nx,ny = w.x+dx, w.y+dy
            if self.wrap:
                nx%=self.cols; ny%=self.rows
            else:
                nx = clamp(nx, 0, self.cols-1); ny = clamp(ny, 0, self.rows-1)
            # Bias weight
            dxn,dyn=dir_vec(d); dot=max(0.0, dxn*bx + dyn*by)
            bias_w = 1.0 + w.bias_strength*dot
            # Territory preference: higher if target cell is similar color or family territory
            cell_col = self.color[ny][nx]
            col_sim = 1 - (color_distance(w_col, cell_col) / (255*math.sqrt(3)))  # Normalized similarity
            terr_str = self.get_territory_strength(w.family_id, nx, ny)
            terr_w = 1 + 2 * (col_sim + terr_str)
            weights.append(bias_w * terr_w)
        return weighted_choice(opts, weights)
    def deposit_scent(self,w,x,y,ttl):
        self.scent_ttl[y][x]=ttl
        dnaR = w.dna_R if w.dna_ready() else [self.color[y][x][0]]*3
        dnaG = w.dna_G if w.dna_ready() else [self.color[y][x][1]]*3
        dnaB = w.dna_B if w.dna_ready() else [self.color[y][x][2]]*3
        self.scent[y][x]=(w.id, tuple(dnaR), tuple(dnaG), tuple(dnaB), tuple(w.bias), w.spawn_scale, w.vigor, w.family_id)
    def interact(self,w,x,y):
        ttl=self.scent_ttl[y][x]; 
        if ttl<=0: return
        info=self.scent[y][x]
        if not info: return
        owner, dnaR,dnaG,dnaB, bias_vec, s_scale, vigor, family_id = info
        if owner==w.id: return
        if random.random()<self.mix:
            tgtR=random.choice(list(dnaR) + (w.dna_R if w.dna_ready() else []))
            tgtG=random.choice(list(dnaG) + (w.dna_G if w.dna_ready() else []))
            tgtB=random.choice(list(dnaB) + (w.dna_B if w.dna_ready() else []))
            w.R.retarget(int(tgtR)); w.G.retarget(int(tgtG)); w.B.retarget(int(tgtB))
            bx=0.8*w.bias[0]+0.2*bias_vec[0]; by=0.8*w.bias[1]+0.2*bias_vec[1]; w.bias=list(norm2(bx,by))
            win_p=clamp(0.5 + 0.2*(w.vigor - vigor),0.05,0.95)
            if random.random()<win_p: w.spawn_scale=clamp(w.spawn_scale*1.05,0.2,4.0)
            else: w.spawn_scale=clamp(w.spawn_scale*0.95,0.2,4.0)
            # Family mixing: small chance to adopt family if different
            if w.family_id != family_id and random.random() < 0.05:
                w.family_id = family_id
    def apply_environment_effect(self, w, x, y):
        bg_col = self.bg_color[y][x]
        w_col = w.average_color()
        dist = color_distance(w_col, bg_col) / (255 * math.sqrt(3))  # Normalized distance
        if dist < 0.3:  # Similar: beneficial
            w.vigor = clamp(w.vigor * 1.01, 0.7, 1.3)
            w.lifespan += 1
        elif dist > 0.7:  # Dissimilar: destructive
            w.vigor = clamp(w.vigor * 0.99, 0.7, 1.3)
            w.lifespan -= 1
    def step(self, smell_ttl):
        updates=[]; newborns=[]
        bg_updates = self.step_background()
        for w in list(self.walkers):
            if not w.alive: continue
            r,g,b=w.rgb()
            w.heading=self.choose_dir(w)
            dx,dy=VEC[w.heading]; nx,ny=w.x+dx, w.y+dy
            if self.wrap:
                nx%=self.cols; ny%=self.rows
            else:
                if nx<0 or nx>=self.cols: w.heading=OPP[w.heading]; dx,dy=VEC[w.heading]; nx=max(0,min(self.cols-1,w.x+dx))
                if ny<0 or ny>=self.rows: w.heading=OPP[w.heading]; dx,dy=VEC[w.heading]; ny=max(0,min(self.rows-1,w.y+dy))
            self.interact(w,nx,ny)
            self.mask[w.y][w.x] |= w.heading
            self.mask[ny][nx] |= OPP[w.heading]
            self.color[w.y][w.x]=(r,g,b); self.color[ny][nx]=(r,g,b)
            updates.append((w.x,w.y)); updates.append((nx,ny))
            self.deposit_scent(w,w.x,w.y,smell_ttl); self.deposit_scent(w,nx,ny,smell_ttl)
            self.update_family_presence(w, w.x, w.y); self.update_family_presence(w, nx, ny)
            self.apply_environment_effect(w, nx, ny)
            w.x,w.y=nx,ny; w.age+=1
            w.record_dna(r,g,b)
            prob,win = self.spawn_base.get(w.depth,(0.0,0))
            prob *= w.spawn_scale * w.vigor  # Boost by vigor
            terr_bonus = (self.get_territory_strength(w.family_id, w.x, w.y) * 2)
            prob *= (1 + terr_bonus)  # Boost in territory
            sid=w.id; self.spawned_steps[sid]=self.spawned_steps.get(sid,0)+1
            if self.spawned_steps[sid]<=win and len(self.walkers)+len(newborns)<self.max_walkers:
                if random.random()<prob:
                    child_rgb=(random.choice(w.dna_R), random.choice(w.dna_G), random.choice(w.dna_B)) if w.dna_ready() else (r,g,b)
                    child_hd=random.choice([d for d in (N,E,S,W) if d!=OPP[w.heading]])
                    newborns.append((w, w.x, w.y, child_hd, child_rgb))
            if w.age>=w.lifespan: w.alive=False
        # age scents
        for y in range(self.rows):
            row=self.scent_ttl[y]
            for x in range(self.cols):
                if row[x]>0:
                    row[x]-=1
                    if row[x]<=0: self.scent[y][x]=None
        for parent,x,y,hd,rgb in newborns:
            self.spawn(x=x,y=y,depth=parent.depth+1,heading=hd,rgb=rgb,parent=parent)
        if updates or bg_updates:
            out=[]
            all_updates = set(updates + bg_updates)
            for x,y in all_updates:
                r,g,b=self.color[y][x]
                br,bg,bb = self.bg_color[y][x]
                glyph = self.glyph(x,y)
                out.append(rgb_bg(br,bg,bb) + rgb_fg(r,g,b) + f"\x1b[{y+1};{x+1}H{glyph}" + RESET)
            sys.stdout.write("".join(out)); sys.stdout.flush()

def main():
    ap=argparse.ArgumentParser(description="Competitive-traits walkers (terminal, modified)")
    ap.add_argument("--style", default="heavy", choices=list(TILES.keys()))
    ap.add_argument("--wrap", action="store_true")
    ap.add_argument("--delay", type=float, default=0.05)
    ap.add_argument("--grad", type=int, default=16)
    ap.add_argument("--lifetime", type=int, default=256)
    ap.add_argument("--smell_ttl", type=int, default=60)
    ap.add_argument("--mix", type=float, default=0.30)
    ap.add_argument("--max_walkers", type=int, default=400)
    ap.add_argument("--seed", type=int, default=None)
    args=ap.parse_args()
    if args.seed is not None: random.seed(args.seed)
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    cols,lines=shutil.get_terminal_size(fallback=(100,34))
    rows=max(8,lines-1); cols=max(40,cols)
    world=World(cols,rows,args.style,args.wrap,args.grad,args.lifetime,args.smell_ttl,args.mix,args.max_walkers)
    biases=((1,-1),(-1,-1),(-1,1),(1,1))
    for i,bv in enumerate(biases):
        bx,by=norm2(*bv)
        rgb=(random.randint(0,255),random.randint(0,255),random.randint(0,255))
        x=(i+1)*cols//5; y=rows//2
        w=Walker(x,y,heading=random.choice((N,E,S,W)),depth=0,rgb=rgb,grad=args.grad,style=args.style,lifespan=args.lifetime,
                 bias=(bx,by),bias_strength=random.uniform(0.25,0.7),spawn_scale=1.0,vigor=random.uniform(0.9,1.1))
        world.walkers.append(w)
    hide="\x1b[?25l"; show="\x1b[?25h"; clear="\x1b[2J"
    sys.stdout.write(hide+clear); sys.stdout.flush()
    try:
        while True:
            world.step(args.smell_ttl)
            if args.delay>0: time.sleep(args.delay)
            ncols,nlines=shutil.get_terminal_size(fallback=(cols,lines))
            if ncols!=cols or nlines!=lines:
                cols,lines=ncols,nlines
                rows=max(8,lines-1); cols=max(40,cols)
                world=World(cols,rows,args.style,args.wrap,args.grad,args.lifetime,args.smell_ttl,args.mix,args.max_walkers)
                for i,bv in enumerate(biases):
                    bx,by=norm2(*bv)
                    rgb=(random.randint(0,255),random.randint(0,255),random.randint(0,255))
                    x=(i+1)*cols//5; y=rows//2
                    w=Walker(x,y,heading=random.choice((N,E,S,W)),depth=0,rgb=rgb,grad=args.grad,style=args.style,lifespan=args.lifetime,
                             bias=(bx,by),bias_strength=random.uniform(0.25,0.7),spawn_scale=1.0,vigor=random.uniform(0.9,1.1))
                    world.walkers.append(w)
                sys.stdout.write(clear); sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m"+show+"\n"); sys.stdout.flush()

if __name__=="__main__":
    main()