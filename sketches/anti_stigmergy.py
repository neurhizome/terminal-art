#!/usr/bin/env python3
"""
Anti-stigmergy sketch.

Two modes to compare:

  --mode avoid   Walkers deposit positive scent, flee high-gradient areas.
                 The field saturates; walkers scatter to find low-signal refuge.

  --mode bleach  Walkers drain signal at their position and flee high-gradient areas.
                 The field is actively carved. Does avoidance produce different
                 spatial structure than erasure?

Prediction: bleaching creates persistent low-signal corridors that attract
later walkers; avoidance creates uniform saturation with no memory of paths.
Run both and watch what survives.
"""

import argparse
import random
import time

from src.automata import Spawner
from src.genetics import Genome
from src.fields import DiffusionField
from src.automata.behaviors import GradientFollow, RandomWalk
from src.renderers import TerminalStage


def run(mode: str, n_walkers: int, deposit_strength: float, ticks: int):
    stage = TerminalStage()
    W, H = stage.width, stage.height

    scent = DiffusionField(W, H, diffusion_rate=0.15, decay_rate=0.97)
    behavior = GradientFollow(field_name='scent', attraction=False, sensitivity=1.2)
    fallback = RandomWalk()

    spawner = Spawner(max_walkers=n_walkers, width=W, height=H)
    for _ in range(n_walkers):
        hue = random.random()
        spawner.spawn_random(genome=Genome(color_h=hue, vigor=random.uniform(0.4, 1.0)))

    # Seed a non-uniform starting field so walkers have something to react to.
    for _ in range(W * H // 4):
        sx = random.randint(0, W - 1)
        sy = random.randint(0, H - 1)
        scent.deposit(sx, sy, random.uniform(0.3, 1.0))

    tick = 0
    try:
        while ticks == 0 or tick < ticks:
            scent.update()

            for walker in spawner.walkers:
                # Deposit or bleach at current position.
                amount = walker.vigor * deposit_strength
                if mode == 'bleach':
                    scent.bleach(walker.x, walker.y, amount)
                else:
                    scent.deposit(walker.x, walker.y, amount * 0.3)

                dx, dy = behavior.get_move(walker.x, walker.y, field=scent)
                walker.move(dx, dy, W, H, wrap=True)

            stage.render_field(scent)
            stage.render_walkers(spawner.walkers)
            stage.flush()

            tick += 1
            time.sleep(0.04)

    except KeyboardInterrupt:
        pass
    finally:
        stage.clear()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--mode', choices=['avoid', 'bleach'], default='bleach',
                   help='avoid: positive deposit + repulsion; bleach: active drain + repulsion')
    p.add_argument('--walkers', type=int, default=80)
    p.add_argument('--deposit', type=float, default=0.5,
                   help='Deposit/bleach strength per tick')
    p.add_argument('--ticks', type=int, default=0,
                   help='Run for N ticks then exit (0 = run until Ctrl-C)')
    args = p.parse_args()
    run(args.mode, args.walkers, args.deposit, args.ticks)


if __name__ == '__main__':
    main()
