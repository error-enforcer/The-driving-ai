import sys
import os
import time
import keyboard

"""
*Ai
"""
"""
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import tensorflow
"""

"""
#Game
"""
import numpy as np
import pyglet
from pyglet import *
from pyglet.window import *
from pyglet.gl import *
from pyglet.shapes import *

# --- Renderer class: manages window and batch ---
class Renderer:
    def __init__(self, width=1280, height=720):
        self.window = pyglet.window.Window(width=width, height=height, caption="Simple Car Game")
        pyglet.gl.glClearColor(0.5, 0.5, 0.5, 1)  # Background color gray
        self.batch = pyglet.graphics.Batch()
        self.track = Track(self.batch)


# --- Track class: contains walls and checkpoints ---
class Track:
    def __init__(self, batch):
        self.batch = batch
        self.walls = []
        self.create_walls()

    def create_walls(self):
        # Define walls as white rectangles on the batch
        self.walls = [
            Rectangle(300, 300, 600, 20, color=(255, 255, 255), batch=self.batch),
            Rectangle(300, 300, 20, 400, color=(255, 255, 255), batch=self.batch),
            # Add more walls if needed
        ]


# --- Player class: handles movement, rotation, collision ---
class Player:
    def __init__(self, x, y, batch):
        self.x = x
        self.y = y
        self.speed = 0
        self.rotation = 0  # degrees

        # Visual representation of the player (a red rectangle)
        self.shape = Rectangle(x, y, 20, 40, color=(255, 0, 0), batch=batch)
        self.shape.anchor_x = self.shape.width // 2
        self.shape.anchor_y = self.shape.height // 2

        # Movement parameters
        self.rotation_speed = 210   # degrees per second
        self.accel_rate = 100
        self.decel_rate = 80
        self.braking_rate = 50
        self.max_speed = 500
        self.reverse_speed = -100

    def move(self, dt, keys, walls):
        # Handle rotation
        if keys[key.A]:
            self.rotation -= self.rotation_speed * dt
        if keys[key.D]:
            self.rotation += self.rotation_speed * dt

        # Handle acceleration / deceleration
        if keys[key.W]:
            self.speed += 3 + self.accel_rate * dt
        elif keys[key.S]:
            self.speed -= 3 + self.braking_rate * dt
        elif keys[key.SPACE]:
            self.speed -= 10 + self.braking_rate * dt
            self.speed = max(self.speed, 0)
        else:
            # Natural friction slows the player
            if self.speed > 0:
                self.speed -= self.decel_rate * dt
                self.speed = max(self.speed, 0)
            elif self.speed < 0:
                self.speed += self.decel_rate * dt
                self.speed = min(self.speed, 0)

        # Clamp speed to max/min limits
        self.speed = max(self.reverse_speed, min(self.speed, self.max_speed))

        # Calculate intended movement
        radians = np.radians(self.rotation)
        dx = np.sin(radians) * self.speed * dt
        dy = np.cos(radians) * self.speed * dt

        # Check collisions on X axis
        new_x = self.x + dx
        if not self._collides(new_x, self.y, walls):
            self.x = new_x
        else:
            self.speed *= 0.5  # Reduce speed on collision

        # Check collisions on Y axis
        new_y = self.y + dy
        if not self._collides(self.x, new_y, walls):
            self.y = new_y
        else:
            self.speed *= 0.5

        # Update the visual position and rotation
        self.shape.x = self.x
        self.shape.y = self.y
        self.shape.rotation = self.rotation

    def _collides(self, x, y, walls):
        # Simple AABB collision detection with a reduced collision box (1/3 size)
        collision_box_width = self.shape.width / 3
        collision_box_height = self.shape.height / 3

        for wall in walls:
            if (
                x + collision_box_width > wall.x and
                x - collision_box_width < wall.x + wall.width and
                y + collision_box_height > wall.y and
                y - collision_box_height < wall.y + wall.height
            ):
                return True
        return False


# --- Main function to setup and run the game ---
def main():
    renderer = Renderer()
    player = Player(100, 100, renderer.batch)

    keys = key.KeyStateHandler()
    renderer.window.push_handlers(keys)

    def update(dt):
        player.move(dt, keys, renderer.track.walls)

    @renderer.window.event
    def on_draw():
        renderer.window.clear()
        renderer.batch.draw()

    pyglet.clock.schedule_interval(update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()