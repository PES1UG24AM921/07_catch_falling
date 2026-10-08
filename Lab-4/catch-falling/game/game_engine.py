"""
GameEngine: owns the basket and all falling objects.

Tasks 1-4 are done: catch detection, basket boundaries and movement,
controlled spawning, and a temporary SPACE speed boost with a cooldown.
"""

import random
import pygame

from game.basket import Basket
from game.falling_object import FallingObject
from game.collision import is_caught
from game.renderer import WIDTH, HEIGHT

MIN_SPAWN_INTERVAL = 30      # frames between spawns, picked at random
MAX_SPAWN_INTERVAL = 70      # from this range
MAX_OBJECTS = 6              # most objects allowed on screen at once
MIN_SPAWN_DISTANCE = 60      # new spawn must be this far (px) from the last
OBJECT_RADIUS = 14           # keeps spawns fully inside the screen
BOOST_DURATION_FRAMES = 180  # ~3 seconds at 60 FPS
BOOST_COOLDOWN_FRAMES = 300  # ~5 seconds after a boost ends
MAX_MISSES = 5


class GameEngine:
    def __init__(self):
        self.basket = Basket(x=WIDTH / 2, y=HEIGHT - 30)
        self.objects = []
        self.frames_until_spawn = 0
        self.last_spawn_x = None
        self.boost_cooldown = 0
        self.score = 0
        self.misses = 0
        self.game_over = False

    def _pick_spawn_x(self):
        """Random x inside the screen, not too close to the last spawn."""
        x = random.randint(OBJECT_RADIUS, WIDTH - OBJECT_RADIUS)
        for _ in range(10):
            if self.last_spawn_x is None or abs(x - self.last_spawn_x) >= MIN_SPAWN_DISTANCE:
                break
            x = random.randint(OBJECT_RADIUS, WIDTH - OBJECT_RADIUS)
        return x

    def _spawn_object(self):
        x = self._pick_spawn_x()
        self.last_spawn_x = x
        self.objects.append(FallingObject(x=x, y=-OBJECT_RADIUS, speed=3))

    def handle_input(self, keys_pressed):
        if self.game_over:
            return
        # keys_pressed is the *held* state (pygame.key.get_pressed()), so
        # the basket moves every frame a key stays down. Holding both
        # keys cancels out to no movement.
        direction = int(bool(keys_pressed[pygame.K_RIGHT])) - int(bool(keys_pressed[pygame.K_LEFT]))
        self.basket.x += direction * self.basket.speed

        # basket.x is the basket's centre, so keep the whole basket on
        # screen by clamping the centre to half a width from each edge.
        half_width = self.basket.width / 2
        self.basket.x = max(half_width, min(WIDTH - half_width, self.basket.x))

    def handle_keydown(self, key):
        if self.game_over and key == pygame.K_r:
            self.__init__()
        elif key == pygame.K_SPACE and not self.game_over:
            if not self.basket.is_boosted and self.boost_cooldown == 0:
                self.basket.activate_boost(BOOST_DURATION_FRAMES)

    def update(self):
        if self.game_over:
            return

        self.frames_until_spawn -= 1
        if self.frames_until_spawn <= 0:
            if len(self.objects) < MAX_OBJECTS:
                self._spawn_object()
            self.frames_until_spawn = random.randint(MIN_SPAWN_INTERVAL, MAX_SPAWN_INTERVAL)

        for obj in self.objects:
            obj.update()

        # Count the boost down; start the cooldown the frame it expires.
        was_boosted = self.basket.is_boosted
        self.basket.update_boost()
        if was_boosted and not self.basket.is_boosted:
            self.boost_cooldown = BOOST_COOLDOWN_FRAMES
        elif self.boost_cooldown > 0:
            self.boost_cooldown -= 1

        # Split objects into caught / not caught in one pass, then rebuild
        # the list, so nothing is removed from the list while iterating it.
        basket_rect = self.basket.get_rect()
        remaining = []
        for obj in self.objects:
            if is_caught(basket_rect, obj):
                self.score += 1
            else:
                remaining.append(obj)
        self.objects = remaining

        missed = [o for o in self.objects if o.is_past_bottom(HEIGHT)]
        if missed:
            self.objects = [o for o in self.objects if not o.is_past_bottom(HEIGHT)]
            self.misses += len(missed)
            if self.misses >= MAX_MISSES:
                self.game_over = True

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_scene(surface, self.basket, self.objects)
        renderer.draw_text(surface, font, f"Score: {self.score}", (10, 10))
        renderer.draw_text(surface, font, f"Misses: {self.misses}/{MAX_MISSES}", (10, 36))

        if self.basket.is_boosted:
            seconds_left = self.basket.boosted_frames / 60
            renderer.draw_text(surface, font, f"BOOST! {seconds_left:.1f}s", (10, 62),
                               renderer.COLOR_BOOST_TEXT)
        elif self.boost_cooldown > 0:
            renderer.draw_text(surface, font, f"Boost cooldown: {self.boost_cooldown / 60:.1f}s", (10, 62))
        else:
            renderer.draw_text(surface, font, "Boost ready (SPACE)", (10, 62))

        if self.game_over:
            renderer.draw_banner(surface, font, f"Game Over! Final score: {self.score}. Press R to restart.")
            