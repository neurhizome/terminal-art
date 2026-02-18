#!/usr/bin/env python3
"""
sketchbook.py - Quick experimentation helpers

Makes it trivial to try new ideas without boilerplate.
Focus on the creative part, not the setup.
"""

import sys
import time
import random
from typing import Optional, List, Literal
from dataclasses import dataclass, field

from src.automata import Walker, Spawner, RandomWalk, GradientFollow, LevyFlight, BiasedWalk
from src.genetics import Genome
from src.fields import DiffusionField, TerritoryField
from src.events import EventScheduler, PeriodicEventSpawner, AESTHETIC_POOL, CHAOS_POOL, COMPETITIVE_POOL
from src.renderers.terminal_stage import TerminalStage
from src.capture import quick_capture
from src.keyboard import KeyboardInput


@dataclass
class QuickSketch:
    """
    Minimal setup for rapid experimentation.

    Usage:
        sketch = quick_sketch(walkers=200, colors='rainbow')
        sketch.mutation_rate = 0.1
        sketch.run()
    """

    # Population
    n_walkers: int = 200
    max_walkers: int = 500

    # Genetics
    colors: Literal['rainbow', 'random', 'single', 'evenly_spaced'] = 'random'
    base_hue: float = 0.0
    mutation_rate: float = 0.03
    breeding_threshold: float = 0.25

    # Movement
    behavior: Literal['random', 'levy', 'gradient', 'biased'] = 'random'
    eight_way: bool = True

    # Spawning
    spawn_rate: float = 0.08
    breed_radius: float = 6.0

    # Death
    max_age: Optional[int] = 800
    vigor_threshold: float = 0.2

    # Fields
    fields: List[str] = field(default_factory=lambda: ['territory'])
    diffusion_rate: float = 0.2
    decay_rate: float = 0.95
    chunk_size: int = 8

    # Events
    events: bool = False
    event_pool: Literal['aesthetic', 'chaos', 'competitive', 'gentle'] = 'aesthetic'
    event_interval: tuple = (200, 500)

    # Rendering
    delay: float = 0.03

    # Seed
    seed: Optional[int] = None

    def __post_init__(self):
        if self.seed is not None:
            random.seed(self.seed)

    def run(self):
        """Run the sketch"""
        with TerminalStage() as stage:
            width, height = stage.width, stage.height

            # Setup spawner
            spawner = Spawner(max_walkers=self.max_walkers, width=width, height=height)

            # Setup fields
            scent_field = None
            territory_field = None

            if 'diffusion' in self.fields or 'scent' in self.fields:
                scent_field = DiffusionField(width, height, self.diffusion_rate, self.decay_rate)

            if 'territory' in self.fields:
                territory_field = TerritoryField(width, height, chunk_size=self.chunk_size)

            # Setup behavior
            if self.behavior == 'random':
                behavior = RandomWalk(eight_way=self.eight_way)
            elif self.behavior == 'levy':
                behavior = LevyFlight()
            elif self.behavior == 'gradient' and scent_field:
                behavior = GradientFollow('scent', attraction=True)
            elif self.behavior == 'biased':
                behavior = BiasedWalk((1, 0), bias_strength=0.5)
            else:
                behavior = RandomWalk(eight_way=self.eight_way)

            # Spawn initial population
            self._spawn_initial(spawner, width, height)

            # Setup events
            event_scheduler = None
            periodic_spawner = None

            if self.events:
                event_scheduler = EventScheduler()

                pool_map = {
                    'aesthetic': AESTHETIC_POOL,
                    'chaos': CHAOS_POOL,
                    'competitive': COMPETITIVE_POOL,
                }
                event_pool = pool_map.get(self.event_pool, AESTHETIC_POOL)

                periodic_spawner = PeriodicEventSpawner(
                    event_scheduler,
                    event_pool,
                    interval_range=self.event_interval
                )

            # Main loop
            tick = 0
            paused = False
            capture_count = 0

            # Setup keyboard input
            kb = KeyboardInput()
            kb.start()

            try:
                while True:
                    # Handle keyboard input
                    key = kb.get_key()
                    if key:
                        if key == 'q':
                            break
                        elif key == 'c':
                            # Capture screenshot!
                            filepath = quick_capture(
                                stage,
                                f"capture_{capture_count:03d}",
                                description=f"Captured at tick {tick}",
                                script="sketchbook",
                                seed=self.seed,
                                tick=tick,
                                params={
                                    'walkers': len(spawner.walkers),
                                    'mutation_rate': self.mutation_rate,
                                    'spawn_rate': self.spawn_rate,
                                }
                            )
                            capture_count += 1
                            # Show notification (will be visible briefly)
                            sys.stdout.write(f"\x1b[{height+2};1H📸 Captured: {filepath}\x1b[K")
                            sys.stdout.flush()
                            time.sleep(0.5)
                        elif key == 'p':
                            paused = not paused
                        elif key == '+':
                            self.spawn_rate = min(1.0, self.spawn_rate + 0.01)
                        elif key == '-':
                            self.spawn_rate = max(0.0, self.spawn_rate - 0.01)
                        elif key == 'm':
                            self.mutation_rate = max(0.0, self.mutation_rate - 0.01)
                        elif key == 'M':
                            self.mutation_rate = min(1.0, self.mutation_rate + 0.01)
                        elif key in ('?', 'h'):
                            # Show help (will be visible briefly)
                            help_text = (
                                "Controls: c=capture p=pause +/-=spawn m/M=mutation q=quit"
                            )
                            sys.stdout.write(f"\x1b[{height+2};1H{help_text}\x1b[K")
                            sys.stdout.flush()
                            time.sleep(1.5)

                    if paused:
                        time.sleep(0.1)
                        continue
                    # Update
                    spawner.age_all()

                    # Walker actions
                    for walker in spawner.walkers:
                        # Deposit scent
                        if scent_field:
                            scent_field.deposit(walker.x, walker.y, walker.vigor * 0.5)

                        # Claim territory
                        if territory_field:
                            territory_field.claim(walker)

                        # Move
                        if self.behavior == 'gradient' and scent_field:
                            dx, dy = behavior.get_move(walker.x, walker.y, field=scent_field)
                        else:
                            dx, dy = behavior.get_move(walker.x, walker.y)

                        walker.move(dx, dy, width, height, wrap=True)

                    # Reproduction
                    if not spawner.is_full() and random.random() < self.spawn_rate:
                        walker = random.choice(spawner.walkers)
                        partners = spawner.find_breeding_partners(
                            walker,
                            self.breed_radius,
                            threshold=self.breeding_threshold
                        )

                        if partners:
                            partner = random.choice(partners)
                            spawner.spawn_from_parents(
                                walker, partner,
                                mutation_rate=self.mutation_rate
                            )

                    # Death
                    spawner.remove_dead(max_age=self.max_age, vigor_threshold=self.vigor_threshold)

                    # Update fields
                    if scent_field:
                        scent_field.update()
                    if territory_field:
                        territory_field.update()
                        active_ids = {id(w) for w in spawner.walkers}
                        territory_field.prune_genomes(active_ids)

                    # Update events
                    if event_scheduler:
                        system = {
                            'spawner': spawner,
                            'field': scent_field,
                            'config': {
                                'spawn_rate': self.spawn_rate,
                                'mutation_rate': self.mutation_rate,
                            }
                        }
                        event_scheduler.update(system)
                        periodic_spawner.update()

                    # Render
                    stage.clear()

                    # Background: Territory or scent
                    if territory_field:
                        territory_render = territory_field.render()
                        for y in range(height):
                            for x in range(width):
                                _, _, bg = territory_render[y][x]
                                stage.cells[y][x].bg_color = bg
                    elif scent_field:
                        scent_render = scent_field.render()
                        for y in range(height):
                            for x in range(width):
                                _, _, bg = scent_render[y][x]
                                stage.cells[y][x].bg_color = (bg[0]//3, bg[1]//3, bg[2]//3)

                    # Foreground: Walkers
                    for walker in spawner.walkers:
                        if 0 <= walker.x < width and 0 <= walker.y < height:
                            r, g, b = walker.genome.to_rgb()
                            stage.cells[walker.y][walker.x].char = '●'
                            stage.cells[walker.y][walker.x].fg_color = (r, g, b)

                    # Status
                    stats = spawner.get_stats()
                    status = (
                        f"Tick: {tick:6d} | "
                        f"Pop: {stats['count']:3d}/{self.max_walkers} | "
                        f"Age: {stats['avg_age']:.1f} | "
                        f"Vigor: {stats['avg_vigor']:.2f} | "
                        f"Spawn: {self.spawn_rate:.2f} | "
                        f"Mut: {self.mutation_rate:.2f}"
                    )

                    if paused:
                        status += " | PAUSED"

                    if event_scheduler:
                        status += f" | {event_scheduler.get_status_line()}"

                    # Controls hint
                    controls = "[c]apture [p]ause [+/-]spawn [m/M]mut [?]help [q]uit"

                    stage.render_diff()
                    sys.stdout.write(f"\x1b[{height+1};1H{status}\x1b[K")
                    sys.stdout.write(f"\x1b[{height+2};1H{controls}\x1b[K")
                    sys.stdout.flush()

                    time.sleep(self.delay)
                    tick += 1

            except KeyboardInterrupt:
                pass
            finally:
                kb.stop()

    def _spawn_initial(self, spawner, width, height):
        """Spawn initial population with color scheme"""
        if self.colors == 'rainbow':
            for i in range(self.n_walkers):
                hue = i / self.n_walkers
                genome = Genome(color_h=hue, vigor=random.uniform(0.8, 1.2))
                spawner.spawn_random(genome=genome)

        elif self.colors == 'evenly_spaced':
            # For speciation experiments
            n_species = min(8, self.n_walkers // 10)
            per_species = self.n_walkers // n_species

            for i in range(n_species):
                base_hue = i / n_species
                for _ in range(per_species):
                    hue = (base_hue + random.gauss(0, 0.02)) % 1.0
                    genome = Genome(color_h=hue, vigor=random.uniform(0.8, 1.2))
                    spawner.spawn_random(genome=genome)

        elif self.colors == 'single':
            for _ in range(self.n_walkers):
                genome = Genome(color_h=self.base_hue, vigor=random.uniform(0.8, 1.2))
                spawner.spawn_random(genome=genome)

        else:  # random
            for _ in range(self.n_walkers):
                genome = Genome(color_h=random.random(), vigor=random.uniform(0.8, 1.2))
                spawner.spawn_random(genome=genome)


def quick_sketch(**kwargs) -> QuickSketch:
    """
    Create a quick sketch with minimal boilerplate.

    Examples:
        # Simple random walk
        quick_sketch(walkers=200).run()

        # Rainbow with events
        quick_sketch(walkers=300, colors='rainbow', events=True).run()

        # Speciation experiment
        quick_sketch(
            walkers=200,
            colors='evenly_spaced',
            breeding_threshold=0.15,
            fields=['territory']
        ).run()

        # Gradient flow
        s = quick_sketch(walkers=250, behavior='gradient', fields=['diffusion'])
        s.mutation_rate = 0.1
        s.spawn_rate = 0.15
        s.run()
    """
    return QuickSketch(**kwargs)


# Preset configurations
PRESETS = {
    'meditative': {
        'walkers': 200,
        'colors': 'rainbow',
        'behavior': 'random',
        'mutation_rate': 0.03,
        'spawn_rate': 0.05,
        'fields': ['territory'],
        'events': True,
        'event_pool': 'aesthetic',
        'delay': 0.04,
    },

    'chaotic': {
        'walkers': 300,
        'colors': 'random',
        'behavior': 'levy',
        'mutation_rate': 0.15,
        'spawn_rate': 0.2,
        'fields': ['diffusion', 'territory'],
        'events': True,
        'event_pool': 'chaos',
        'delay': 0.02,
    },

    'competitive': {
        'walkers': 250,
        'colors': 'evenly_spaced',
        'behavior': 'random',
        'breeding_threshold': 0.15,
        'spawn_rate': 0.08,
        'fields': ['territory'],
        'events': True,
        'event_pool': 'competitive',
        'max_age': 600,
        'delay': 0.03,
    },

    'aesthetic': {
        'walkers': 250,
        'colors': 'rainbow',
        'behavior': 'random',
        'mutation_rate': 0.05,
        'spawn_rate': 0.15,
        'fields': ['diffusion', 'territory'],
        'events': True,
        'event_pool': 'aesthetic',
        'max_age': None,  # No death
        'delay': 0.03,
    },

    'flow': {
        'walkers': 300,
        'colors': 'rainbow',
        'behavior': 'levy',
        'mutation_rate': 0.08,
        'spawn_rate': 0.12,
        'fields': ['diffusion'],
        'events': True,
        'event_pool': 'aesthetic',
        'delay': 0.025,
    },
}


def preset(name: str, **overrides) -> QuickSketch:
    """
    Load a preset configuration with optional overrides.

    Available presets:
    - meditative: Calm, flowing, gentle colors
    - chaotic: High energy, fast mutation, Lévy flights
    - competitive: Species battle for territory
    - aesthetic: Pure beauty, no death
    - flow: Fluid motion with color waves

    Example:
        preset('meditative').run()
        preset('chaotic', walkers=500).run()
    """
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")

    config = PRESETS[name].copy()
    config.update(overrides)
    return QuickSketch(**config)
