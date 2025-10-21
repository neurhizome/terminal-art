#!/usr/bin/env python3
# walker_traits_war_3d_bg.py
#
# Riff on walker_traits_war_3d.py: Add background colors to represent fields of influence.
# Background colors are set based on the walker's DNA average and fade over time.
# Added diffusion to spread the background colors, creating spheres/fields of influence.
# Updates now use a set to include all cells with active scents or changes.
import argparse, random, shutil, sys, time, math
from typing import List, Tuple
import copy

N,NE,E,SE,S,SW,W,NW = 1,2,4,8,16,32,64,128
DIRS = (N,NE,E,SE,S,SW,W,NW)
OPP = {N:S, S:N, E:W, W:E, NE:SW, SW:NE, NW:SE, SE:NW}
VEC = {N:(0,-1), NE:(1,-1), E:(1,0), SE:(1,1), S:(0,1), SW:(-1,1), W:(-1,0), NW:(-1,-1)}
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

BIAS_VECTORS = [norm2(*VEC[d]) for d in DIRS]

def dir_vec(d:int):
    dx,dy = VEC[d]; n = math.hypot(dx,dy); return (dx/n, dy/n)

def weighted_choice(opts, weights):
    total = sum(weights); r = random.random()*total
    acc = 0.0
    for o,w in zip(opts,weights):
        acc += w
        if r <= acc: return o
    return opts[-1]

class Walker:
    _next_id = 1
    __slots__=("id","x","y","heading","depth","age","alive",
               "R","G","B","dna_R","dna_G","dna_B","dna_samples",
               "bias","bias_strength","spawn_scale","vigor","lifespan","style")
    def __init__(self, x,y, heading, depth, rgb, grad, style, lifespan,
                 bias=None, bias_strength=None, spawn_scale=1.0, vigor=None):
        self.id = Walker._next_id; Walker._next_id += 1
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

class World:
    def __init__(self, cols, rows, style, wrap, grad, lifetime, smell_ttl, mix, max_walkers):
        self.cols,self.rows = cols,rows
        self.style=style; self.wrap=wrap; self.grad=grad; self.lifetime=lifetime
        self.mix=clamp(mix,0.0,1.0); self.max_walkers=max_walkers
        self.mask=[[0]*cols for _ in range(rows)]
        self.color=[[(220,220,220)]*cols for _ in range(rows)]
        self.bg_color=[[(0,0,0)]*cols for _ in range(rows)]
        self.scent_ttl=[[0]*cols for _ in range(rows)]
        self.scent=[[None]*cols for _ in range(rows)]
        self.walkers=[]; self.spawn_base={0:(0.02,128), 1:(0.005,64), 2:(0.00125,32)}
        self.spawned_steps={}
    def clear(self):
        self.mask=[[0]*self.cols for _ in range(self.rows)]
        self.color=[[(220,220,220)]*self.cols for _ in range(self.rows)]
        self.bg_color=[[(0,0,0)]*self.cols for _ in range(self.rows)]
        self.scent_ttl=[[0]*self.cols for _ in range(self.rows)]
        self.scent=[[None]*self.cols for _ in range(self.rows)]
        self.walkers.clear(); self.spawned_steps.clear()
    def spawn(self, x=None,y=None,depth=0,heading=None,rgb=None,parent=None):
        if len(self.walkers)>=self.max_walkers: return
        if x is None: x=self.cols//2
        if y is None: y=self.rows//2
        if heading is None: heading=random.choice(DIRS)
        if rgb is None: rgb=(random.randint(0,255),random.randint(0,255),random.randint(0,255))
        if parent:
            bx,by=parent.bias
            bx+=random.uniform(-0.25,0.25); by+=random.uniform(-0.25,0.25); bx,by=norm2(bx,by)
            bstr=clamp(parent.bias_strength+random.uniform(-0.05,0.05),0.05,0.85)
            scale=clamp(parent.spawn_scale*(1+random.uniform(-0.1,0.1)),0.25,3.0)
            vigor=clamp(parent.vigor*(1+random.uniform(-0.05,0.05)),0.7,1.3)
        else:
            bx,by=random.choice(BIAS_VECTORS); bstr=random.uniform(0.1,0.6); scale=1.0; vigor=random.uniform(0.85,1.15)
        w=Walker(x,y,heading,depth,rgb,self.grad,self.style,self.lifetime,bias=(bx,by),bias_strength=bstr,spawn_scale=scale,vigor=vigor)
        self.walkers.append(w); self.spawned_steps[w.id]=0
    def glyph(self,x,y):
        mask_val = self.mask[y][x]
        if self.style == "braille":
            return chr(0x2800 + mask_val)
        else:
            # For other styles, ignore diagonal bits and fallback to cardinal directions
            cardinal_mask = mask_val & (N | E | S | W)
            return TILES.get(self.style, TILES["heavy"]).get(cardinal_mask, "X")
    def choose_dir(self,w):
        opts=[d for d in DIRS if d!=OPP.get(w.heading, 0)]
        bx,by=w.bias; weights=[]
        for d in opts:
            dx,dy=dir_vec(d); dot=max(0.0, dx*bx+dy*by)
            weights.append(1.0 + w.bias_strength*dot)
        return weighted_choice(opts, weights)
    def deposit_scent(self,w,x,y,ttl):
        self.scent_ttl[y][x]=ttl
        dnaR = w.dna_R if w.dna_ready() else [self.color[y][x][0]]*3
        dnaG = w.dna_G if w.dna_ready() else [self.color[y][x][1]]*3
        dnaB = w.dna_B if w.dna_ready() else [self.color[y][x][2]]*3
        self.scent[y][x]=(w.id, tuple(dnaR), tuple(dnaG), tuple(dnaB), tuple(w.bias), w.spawn_scale, w.vigor)
        avg_r = sum(dnaR) / 3.0
        avg_g = sum(dnaG) / 3.0
        avg_b = sum(dnaB) / 3.0
        self.bg_color[y][x] = (avg_r, avg_g, avg_b)
    def interact(self,w,x,y):
        ttl=self.scent_ttl[y][x]; 
        if ttl<=0: return
        info=self.scent[y][x]
        if not info: return
        owner, dnaR,dnaG,dnaB, bias_vec, s_scale, vigor = info
        if owner==w.id: return
        if random.random()<self.mix:
            # Memetic element: adopt traits if the other has higher vigor, else blend
            if vigor > w.vigor:
                tgtR=random.choice(dnaR)
                tgtG=random.choice(dnaG)
                tgtB=random.choice(dnaB)
                w.R.retarget(int(tgtR)); w.G.retarget(int(tgtG)); w.B.retarget(int(tgtB))
                w.bias = list(bias_vec)
                w.spawn_scale = clamp((w.spawn_scale + s_scale) / 2, 0.2, 4.0)
            else:
                tgtR=random.choice(list(dnaR) + (w.dna_R if w.dna_ready() else []))
                tgtG=random.choice(list(dnaG) + (w.dna_G if w.dna_ready() else []))
                tgtB=random.choice(list(dnaB) + (w.dna_B if w.dna_ready() else []))
                w.R.retarget(int(tgtR)); w.G.retarget(int(tgtG)); w.B.retarget(int(tgtB))
                bx=0.8*w.bias[0]+0.2*bias_vec[0]; by=0.8*w.bias[1]+0.2*bias_vec[1]; w.bias=list(norm2(bx,by))
            win_p=clamp(0.5 + 0.2*(w.vigor - vigor),0.05,0.95)
            if random.random()<win_p: w.spawn_scale=clamp(w.spawn_scale*1.05,0.2,4.0)
            else: w.spawn_scale=clamp(w.spawn_scale*0.95,0.2,4.0)
    def diffuse_bg(self, updates):
        new_bg = copy.deepcopy(self.bg_color)
        for y in range(self.rows):
            for x in range(self.cols):
                ar, ag, ab = self.bg_color[y][x]
                count = 1
                neighbors = []
                for d in DIRS:
                    nx = x + VEC[d][0]
                    ny = y + VEC[d][1]
                    if self.wrap:
                        nx %= self.cols
                        ny %= self.rows
                    elif not (0 <= nx < self.cols and 0 <= ny < self.rows):
                        continue
                    br, bg_, bb = self.bg_color[ny][nx]
                    ar += br
                    ag += bg_
                    ab += bb
                    count += 1
                new_bg[y][x] = (ar / count, ag / count, ab / count)
                if self.scent_ttl[y][x] == 0:
                    nr, ng, nb = new_bg[y][x]
                    new_bg[y][x] = (nr * 0.95, ng * 0.95, nb * 0.95)
                updates.add((x, y))
        self.bg_color = new_bg
    def step(self, smell_ttl):
        updates = set()
        newborns=[]
        for w in list(self.walkers):
            if not w.alive: continue
            r,g,b=w.rgb()
            w.heading=self.choose_dir(w)
            dx,dy=VEC[w.heading]; nx,ny=w.x+dx, w.y+dy
            if self.wrap:
                nx%=self.cols; ny%=self.rows
            else:
                if nx<0 or nx>=self.cols: w.heading=OPP.get(w.heading, w.heading); dx,dy=VEC[w.heading]; nx=max(0,min(self.cols-1,w.x+dx))
                if ny<0 or ny>=self.rows: w.heading=OPP.get(w.heading, w.heading); dx,dy=VEC[w.heading]; ny=max(0,min(self.rows-1,w.y+dy))
            self.interact(w,nx,ny)
            self.mask[w.y][w.x] |= w.heading
            self.mask[ny][nx] |= OPP.get(w.heading, w.heading)
            self.color[w.y][w.x]=(r,g,b); self.color[ny][nx]=(r,g,b)
            updates.add((w.x,w.y)); updates.add((nx,ny))
            self.deposit_scent(w,w.x,w.y,smell_ttl); self.deposit_scent(w,nx,ny,smell_ttl)
            w.x,w.y=nx,ny; w.age+=1
            w.record_dna(r,g,b)
            prob,win = self.spawn_base.get(w.depth,(0.0,0))
            prob *= w.spawn_scale
            sid=w.id; self.spawned_steps[sid]=self.spawned_steps.get(sid,0)+1
            if self.spawned_steps[sid]<=win and len(self.walkers)+len(newborns)<self.max_walkers:
                if random.random()<prob:
                    child_rgb=(random.choice(w.dna_R), random.choice(w.dna_G), random.choice(w.dna_B)) if w.dna_ready() else (r,g,b)
                    child_hd=random.choice([d for d in DIRS if d!=OPP.get(w.heading, 0)])
                    newborns.append((w, w.x, w.y, child_hd, child_rgb))
            if w.age>=w.lifespan: w.alive=False
        # age scents
        for y in range(self.rows):
            row=self.scent_ttl[y]
            for x in range(self.cols):
                if row[x]>0:
                    updates.add((x,y))
                    row[x]-=1
                    if row[x]<=0: self.scent[y][x]=None
        # diffuse bg
        self.diffuse_bg(updates)
        for parent,x,y,hd,rgb in newborns:
            self.spawn(x=x,y=y,depth=parent.depth+1,heading=hd,rgb=rgb,parent=parent)
        if updates:
            out=[]
            for x,y in updates:
                r,g,b=self.color[y][x]
                br,bg_,bb=self.bg_color[y][x]
                out.append(f"\x1b[{y+1};{x+1}H{rgb_bg(br,bg_,bb)}{rgb_fg(r,g,b)}{self.glyph(x,y)}{RESET}")
            sys.stdout.write("".join(out)); sys.stdout.flush()
    def render_all(self):
        out=[]
        for y in range(self.rows):
            for x in range(self.cols):
                r,g,b=self.color[y][x]
                br,bg_,bb=self.bg_color[y][x]
                out.append(f"\x1b[{y+1};{x+1}H{rgb_bg(br,bg_,bb)}{rgb_fg(r,g,b)}{self.glyph(x,y)}{RESET}")
        sys.stdout.write("".join(out)); sys.stdout.flush()

def main():
    ap=argparse.ArgumentParser(description="Competitive-traits walkers (terminal) with higher-dimensional glyph mapping and background fields")
    ap.add_argument("--style", default="braille", choices=list(TILES.keys()) + ["braille"])
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
    for i, bv in enumerate(BIAS_VECTORS):
        bx, by = bv
        rgb=(random.randint(0,255),random.randint(0,255),random.randint(0,255))
        x=(i+1)*cols//(len(BIAS_VECTORS) + 1); y=rows//2
        w=Walker(x,y,heading=random.choice(DIRS),depth=0,rgb=rgb,grad=args.grad,style=args.style,lifespan=args.lifetime,
                 bias=(bx,by),bias_strength=random.uniform(0.25,0.7),spawn_scale=1.0,vigor=random.uniform(0.9,1.1))
        world.walkers.append(w)
    hide="\x1b[?25l"; show="\x1b[?25h"; clear="\x1b[2J"
    sys.stdout.write(hide+clear); sys.stdout.flush()
    world.render_all()
    try:
        while True:
            world.step(args.smell_ttl)
            if args.delay>0: time.sleep(args.delay)
            ncols,nlines=shutil.get_terminal_size(fallback=(cols,lines))
            if ncols!=cols or nlines!=lines:
                cols,lines=ncols,nlines
                rows=max(8,lines-1); cols=max(40,cols)
                world=World(cols,rows,args.style,args.wrap,args.grad,args.lifetime,args.smell_ttl,args.mix,args.max_walkers)
                for i, bv in enumerate(BIAS_VECTORS):
                    bx, by = bv
                    rgb=(random.randint(0,255),random.randint(0,255),random.randint(0,255))
                    x=(i+1)*cols//(len(BIAS_VECTORS) + 1); y=rows//2
                    w=Walker(x,y,heading=random.choice(DIRS),depth=0,rgb=rgb,grad=args.grad,style=args.style,lifespan=args.lifetime,
                             bias=(bx,by),bias_strength=random.uniform(0.25,0.7),spawn_scale=1.0,vigor=random.uniform(0.9,1.1))
                    world.walkers.append(w)
                sys.stdout.write(clear); sys.stdout.flush()
                world.render_all()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[0m"+show+"\n"); sys.stdout.flush()

if __name__=="__main__":
    main()