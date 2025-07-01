import sys
import os
import time
import keyboard

# --- AI import (commented out for now) ---
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense
# import tensorflow
from ai_car import *

# --- Game imports ---
import numpy as np
import pyglet
from pyglet import *
from pyglet.window import *
from pyglet.gl import *
from pyglet.shapes import *
from pyglet.image import load as pyglet_load
from PIL import Image  # Requires `pip install pillow`

# --- Track class ---
class Track:
    def __init__(self, image_path="track.png", batch=None):
        self.image_path = image_path
        self.track_image_pil = Image.open(image_path).convert("L")
        self.width, self.height = self.track_image_pil.size
        self.pixels = self.track_image_pil.load()

        self.track_texture = pyglet.image.load(image_path)
        self.sprite = pyglet.sprite.Sprite(self.track_texture, x=0, y=0, batch=batch)

    def is_driveable(self, x, y):
        if 0 <= int(x) < self.width and 0 <= int(y) < self.height:
            flipped_y = self.height - int(y) - 1  # Convert pyglet y to PIL y
            brightness = self.pixels[int(x), flipped_y]
            return brightness < 128  # black = driveable
        return False


# --- Renderer class ---
class Renderer:
    def __init__(self, width=1700, height=800):
        self.window = pyglet.window.Window(width=width, height=height, caption="Car Game with AI")
        pyglet.gl.glClearColor(0.5, 0.5, 0.5, 1)  # Gray background
        self.batch = pyglet.graphics.Batch()
        self.track = Track("track.png", batch=self.batch)


# --- Player class ---
class Player:
    def __init__(self, x, y, batch, default_rotation):
        self.x = x
        self.y = y
        self.speed = 0
        self.rotation = default_rotation  # degrees

        self.shape = Rectangle(x, y, 20, 40, color=(255, 0, 0), batch=batch)
        self.shape.anchor_x = self.shape.width // 2
        self.shape.anchor_y = self.shape.height // 2

        # Movement parameters
        self.rotation_speed = 200
        self.accel_rate = 100
        self.decel_rate = 80
        self.braking_rate = 50
        self.max_speed = 500
        self.reverse_speed = -100

    def is_aabb_driveable(self, track, x, y):
        half_w = 10
        half_h = 10
        
        corners = [
            (x - half_w, y - half_h),
            (x - half_w, y + half_h),
            (x + half_w, y - half_h),
            (x + half_w, y + half_h),
        ]
        return all(track.is_driveable(cx, cy) for cx, cy in corners)

    def move(self, dt, keys, track):
        turning_factor = max(0.1, 2 - abs(self.speed) / self.max_speed)
        # Rotation
        if keys[key.A]:
            if self.speed > 0:
                self.rotation -= self.rotation_speed * turning_factor * dt
            elif self.speed < 0:
                self.rotation -= self.rotation_speed * turning_factor * 0.5 * dt

        if keys[key.D]:
            if self.speed > 0:
                self.rotation += self.rotation_speed * turning_factor * dt
            elif self.speed < 0:
                self.rotation += self.rotation_speed * turning_factor * 0.5 * dt

        # Acceleration / Deceleration
        if keys[key.W]:
            self.speed += 1 + self.accel_rate * dt
        elif keys[key.S]:
            self.speed -= 10 + self.braking_rate * dt
        elif keys[key.SPACE]:
            self.speed -= 10 + self.braking_rate * dt
            self.speed = max(self.speed, 0)
        else:
            if self.speed > 0:
                self.speed -= self.decel_rate * dt
                self.speed = max(self.speed, 0)
            elif self.speed < 0:
                self.speed += self.decel_rate * dt
                self.speed = min(self.speed, 0)

        # Clamp speed
        self.speed = max(self.reverse_speed, min(self.speed, self.max_speed))

        # Calculate new position
        radians = np.radians(self.rotation)
        dx = np.sin(radians) * self.speed * dt
        dy = np.cos(radians) * self.speed * dt
        new_x = self.x + dx
        new_y = self.y + dy

        # Check full move collision
        if self.is_aabb_driveable(track, new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            # Try moving only in X
            if self.is_aabb_driveable(track, self.x + dx, self.y):
                self.x += dx
                self.speed *= 0.9  # reduce speed less harshly
            # Try moving only in Y
            elif self.is_aabb_driveable(track, self.x, self.y + dy):
                self.y += dy
                self.speed *= 0.9
            else:
                # Full stop if can't move even on one axis
                self.speed *= 0.3  # reduce speed more

        # Update visual
        self.shape.x = self.x
        self.shape.y = self.y
        self.shape.rotation = self.rotation



# --- Main function ---
def main():
    renderer = Renderer()
    player = Player(600, 100, renderer.batch, 90)

    keys = key.KeyStateHandler()
    renderer.window.push_handlers(keys)

    def update(dt):
        player.move(dt, keys, renderer.track)

    @renderer.window.event
    def on_draw():
        renderer.window.clear()
        renderer.batch.draw()

    pyglet.clock.schedule_interval(update, 1 / 60)
    pyglet.app.run()


# --- Run the game ---
if __name__ == "__main__":
    main()
