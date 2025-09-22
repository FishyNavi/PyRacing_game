# player_utils.py

import math
import os
import pyglet
from pyglet import shapes


class CarState:
    """Manages the state flags and timers for the car."""

    def __init__(self):
        self.drifting = False
        self.crashed = False
        self.is_freecam = False
        self.collision_frames = 0
        self.timer = 0
        self.is_lap_finished = False
        self.lap_started = False
        self.checkpoint_reached = False

    def start_lap(self):
        self.lap_started = True
        self.checkpoint_reached = False
        self.timer = 0
        print("Lap timer started!")

    def reach_checkpoint(self):
        if self.lap_started:
            self.checkpoint_reached = True
            print("Checkpoint reached!")

    def finish_lap(self):
        if self.lap_started and self.checkpoint_reached and self.timer > 1:
            self.is_lap_finished = True
            self.lap_started = False
            self.checkpoint_reached = False
            print("Lap finished!")


class CarPhysics:
    """Handles movement, physics, drift, and angular momentum."""

    def __init__(self, power, friction, speed_cap):
        # Core stats
        self.power = power
        self.friction = friction
        self.speed_cap = speed_cap
        self.reverse_cap = -speed_cap / 3

        # Movement
        self.speed = 0.0
        self.direction = 0.0
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.angular_velocity = 0.0
        self.last_turn = 0

        # Constants(magic numbers :D)
        self.turn_strength = 140
        self.drift_turn_strength = 100
        self.angular_damping = 0.95
        self.collision_spin_force = 20
        self.collision_push_force = 100

        # Cached values
        self._cached_cos = 0.0
        self._cached_sin = 0.0

    def _update_cached_trig(self):
        rad = math.radians(self.direction)
        self._cached_cos = math.cos(rad)
        self._cached_sin = math.sin(rad)

    def update(self, dt, accelerating, braking, turn_input, is_drifting):
        self._update_cached_trig()

        # Acceleration and braking
        if accelerating:
            self.speed += self.power * dt
        if braking:
            factor = 0.5 if self.speed < 0 else 1.0
            self.speed -= self.power * factor * dt

        self.speed = max(self.reverse_cap, min(self.speed, self.speed_cap))

        # Turning
        if turn_input:
            self._apply_turning(dt, turn_input, is_drifting)

        # Drift physics
        self._calculate_drift(dt, is_drifting)

        # Angular momentum from collisions
        self.direction = (self.direction + self.angular_velocity * dt) % 360
        self.angular_velocity *= self.angular_damping
        if abs(self.angular_velocity) < 1.0:
            self.angular_velocity = 0.0

        # Car slow down
        self.vel_x *= 0.995
        self.vel_y *= 0.995

    def _apply_turning(self, dt, turn_input, is_drifting):
        sign = 1 if self.speed >= 0 else -1
        speed_ratio = abs(self.speed) / self.speed_cap

        if not is_drifting:
            self.last_turn = turn_input
            turn_factor = speed_ratio * dt * max(
                1 - self.speed / self.speed_cap / 4, 0.5
            )
            self.direction = (
                self.direction + sign * turn_input * self.turn_strength * turn_factor
            ) % 360
        else:
            drift_turn = (
                sign * self.last_turn * self.drift_turn_strength * speed_ratio * dt
            )
            input_turn = (
                sign * turn_input * self.turn_strength / 2 * speed_ratio * dt
            )
            self.direction = (self.direction + drift_turn + input_turn) % 360

    def _calculate_drift(self, dt, is_drifting):
        if not is_drifting:
            self.vel_x = self.speed * self._cached_cos * dt
            self.vel_y = self.speed * self._cached_sin * dt
            return

        vel_angle = math.atan2(self.vel_y, self.vel_x)
        direction_rad = math.radians(self.direction)
        angle_diff = math.degrees(
            (vel_angle - direction_rad + math.pi) % (2 * math.pi) - math.pi
        )

        diff = abs(angle_diff)
        modded = 90 - abs(90 - diff)
        drift_factor = modded / 90
        self.drift_turn_strength = self.turn_strength * (0.5 + drift_factor)

        ang_diff = (vel_angle - direction_rad + math.pi) % (2 * math.pi) - math.pi
        corr = drift_factor * self.friction * self.speed
        lat_ang = direction_rad + (math.pi / 2 if ang_diff < 0 else -math.pi / 2)
        self.vel_x += math.cos(lat_ang) * corr * dt
        self.vel_y += math.sin(lat_ang) * corr * dt

        fade = drift_factor * 0.01 * (1 - self.speed / self.speed_cap)
        self.vel_x *= 1 - fade
        self.vel_y *= 1 - fade

        measured = math.hypot(self.vel_x, self.vel_y) / dt
        proj = self.vel_x * self._cached_cos + self.vel_y * self._cached_sin
        self.speed = math.copysign(measured, proj)

class CarVisuals:
    """Manages the car's sprite and hitbox."""

    def __init__(self, car_sheet, x, y, scale, batch):
        self.textures = pyglet.image.ImageGrid(car_sheet, rows=1, columns=8)
        for texture in self.textures:
            texture.anchor_x = texture.width // 2
            texture.anchor_y = texture.height // 2

        group = pyglet.graphics.Group(5)
        self.sprite = pyglet.sprite.Sprite(
            self.textures[0], x=x, y=y, batch=batch, group=group
        )
        self.sprite.scale = scale

        hitbox_width = self.sprite.width * 0.8
        hitbox_height = self.sprite.height * 0.4
        self.hitbox = shapes.Rectangle(
            x, y, hitbox_width, hitbox_height, color=(255, 0, 0)
        )
        self.hitbox.anchor_x = hitbox_width / 2
        self.hitbox.anchor_y = hitbox_height / 2
        self.hitbox.opacity = 0 # Hidden
    def update(self, direction, pos_x, pos_y):
        self.sprite.image = self.textures[round(-direction / 45) % 8]
        self.sprite.x = pos_x
        self.sprite.y = pos_y
        self.hitbox.rotation = -direction
        self.hitbox.x = pos_x
        self.hitbox.y = pos_y

    def delete(self):
        self.sprite.delete()


class CarAudio:
    """Manages the engine and collision sounds."""

    def __init__(self, use_pitch_control=True):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine_sound_path = os.path.join(root_dir, "Assets", "engine_loop.wav")
        collision_sound_path = os.path.join(root_dir, "Assets", "collision.mp3")

        try:
            self.collision_sound = pyglet.media.load(collision_sound_path, streaming=False)
        except Exception:
            self.collision_sound = None

        try:
            engine_sound = pyglet.media.load(engine_sound_path, streaming=False)
        except Exception:
            engine_sound = None

        self.engine_player = pyglet.media.Player()
        if engine_sound is not None:
            self.engine_player.queue(engine_sound)
            self.engine_player.loop = True

        self.last_pitch = 1.0
        self.use_pitch_control = use_pitch_control

    def update_pitch(self, speed, speed_cap):
        if not self.use_pitch_control:
            return
        speed_ratio = abs(speed / speed_cap)
        target_pitch = 0.5 + round(speed_ratio, 2)
        if abs(target_pitch - self.last_pitch) > 0.01:
            try:
                self.engine_player.pitch = target_pitch
            except Exception:
                pass
            self.last_pitch = target_pitch

    def play_collision(self):
        if self.collision_sound is not None:
            try:
                self.collision_sound.play()
            except Exception:
                pass

    def delete(self):
        try:
            self.engine_player.delete()
        except Exception:
            pass
