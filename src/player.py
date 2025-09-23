import math
import os
import sys
import pyglet
from pyglet.window import key
from pyglet import shapes


def asset_path(filename):
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root_dir, "Assets", filename)
class Car:
    def __init__(self, car_sheet, window, power, friction, scale, batch):
        # Static parameters

        self.speed = 0
        self.power = power
        self.friction = friction
        self.direction = 0.0
        self.turn_strength = 140
        self.drift_turn_strength = 100
        self.speed_cap = 1000
        self.reverse_cap = -self.speed_cap / 3
        self.batch = pyglet.graphics.Batch()
        self.drifting = False
        self.last_turn = 0
        self.collision_frames = 0
        self.crash_collision_treshold = 500
        self.crashed = False
        self.is_freecam = False
        self.last_pos = 200, 200
        self.timer = 0
        self.is_lap_finished = False
        self.lap_started = False
        self.checkpoint_reached = False
        self.angular_velocity = 0.0
        self.angular_damping = 0.95
        self.collision_spin_force = 20
        self.collision_push_force = 100
        self._cached_direction = None
        self._cached_cos = 0.0
        self._cached_sin = 0.0
        self.x = window.width // 2
        self.y = window.height // 2
        self.hitbox_x = window.width // 2
        self.hitbox_y = window.height // 2
        self.textures = pyglet.image.ImageGrid(car_sheet, rows=1, columns=8)
        self.textures.anchor_x = self.textures.width // 2
        self.textures.anchor_y = self.textures.height // 2
        self.group = pyglet.graphics.Group(5)
        self.sprite = pyglet.sprite.Sprite(
            self.textures[0], x=self.x, y=self.y, batch=batch, group=self.group
        )
        self.sprite.scale = scale
        self.x -= self.sprite.width / 2
        self.y -= self.sprite.height / 2
        self.sprite.x, self.sprite.y = self.x, self.y

        # Movement parameters
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.dx = 0.0
        self.dy = 0.0
        self.smoothx = 0
        self.smoothy = 0

        # Hitbox setup
        hitbox_width = self.sprite.width * 0.8
        hitbox_height = self.sprite.height * 0.4
        self.hitbox = shapes.Rectangle(
            self.hitbox_x,
            self.hitbox_y,
            hitbox_width,
            hitbox_height,
            color=(255, 0, 0),
        )
        self.hitbox.anchor_x = hitbox_width / 2
        self.hitbox.anchor_y = hitbox_height / 2
        self.hitbox.opacity = 0 # Hidden by default

        self.hitbox_corners = [
            shapes.Circle(0, 0, radius=3, color=(0, 255, 0)) for _ in range(4)
        ]

        # Load sounds
        self.collision = pyglet.media.load(asset_path("collision.mp3"), streaming=False)
        engine_sound = pyglet.media.load(asset_path("engine_loop.wav"), streaming=False)
        
        self.engine_player = pyglet.media.Player()
        self.engine_player.queue(engine_sound)
        self.engine_player.loop = True
        self.last_pitch = 1.0

        self.collision_player = pyglet.media.Player()
        self.collision_player.loop = False
        self.update_pitch = self.update_pitch_default

    def _update_cached_trig(self):
        """Cache trigonometric calculations for performance"""
        if self._cached_direction != self.direction:
            self._cached_direction = self.direction
            rad = math.radians(self.direction)
            self._cached_cos = math.cos(rad)
            self._cached_sin = math.sin(rad)

    def update(self, dt, keys):
        if self.update_pitch:
            self.update_pitch()

        self.speed = max(self.reverse_cap, min(self.speed, self.speed_cap))
        turn_left = keys[key.A]
        turn_right = keys[key.D]

        if not self.crashed:
            accelerating = keys[key.W]
            braking = keys[key.S]
            turn_input = (turn_left * 1) + (turn_right * -1)
        else:
            accelerating = False
            braking = False
            turn_input = 0

        self._update_cached_trig()

        turn_rate = self.turn_strength if not self.drifting else self.drift_turn_strength

        if accelerating or braking or self.speed < 0:
            if not self.drifting:
                self.vel_x = self.speed * self._cached_cos * dt
                self.vel_y = self.speed * self._cached_sin * dt

        self.calculate_drift(dt)

        if accelerating:
            self.speed += self.power * dt

        if braking:
            factor = 0.5 if self.speed < 0 else 1.0
            self.speed -= self.power * factor * dt

        if turn_input:
            sign = 1 if self.speed >= 0 else -1
            speed_ratio = abs(self.speed) / self.speed_cap

            if not self.drifting:
                self.last_turn = turn_input
                turn_factor = speed_ratio * dt * max(1 - self.speed / self.speed_cap / 4, 0.5)
                self.direction = (self.direction + sign * turn_input * turn_rate * turn_factor) % 360
            else:
                drift_turn = sign * self.last_turn * self.drift_turn_strength * speed_ratio * dt
                input_turn = sign * turn_input * self.turn_strength / 2 * speed_ratio * dt
                self.direction = (self.direction + drift_turn + input_turn) % 360

        self.direction = (self.direction + self.angular_velocity * dt) % 360
        self.angular_velocity *= self.angular_damping
        if abs(self.angular_velocity) < 1.0:
            self.angular_velocity = 0.0

        self.vel_x *= 0.995
        self.vel_y *= 0.995

        self.sprite.image = self.textures[round(0 - self.direction / 45) % 8]
        self.hitbox.rotation = -self.direction

        up, down, right, left = (keys[key.UP], keys[key.DOWN], keys[key.RIGHT], keys[key.LEFT])
        fcam_h = (left * 1) + (right * -1)
        fcam_v = (down * 1) + (up * -1)

        if self.is_freecam:
            self.dx = -8 * fcam_h
            self.dy = -8 * fcam_v
            alpha = 0.1
            self.smoothx = (1 - alpha) * getattr(self, "smoothx", 0.0) + alpha * self.dx
            self.smoothy = (1 - alpha) * getattr(self, "smoothy", 0.0) + alpha * self.dy
            self.sprite.x -= self.smoothx
            self.sprite.y -= self.smoothy
            self.hitbox.x -= self.smoothx
            self.hitbox.y -= self.smoothy
            self.sprite.x += self.vel_x
            self.sprite.y += self.vel_y
            self.hitbox.x += self.vel_x
            self.hitbox.y += self.vel_y
        else:
            self.dx, self.dy = self.vel_x, self.vel_y
            self.smoothx, self.smoothy = self.vel_x, self.vel_y
            self.sprite.x, self.sprite.y = self.x, self.y
            self.hitbox.x, self.hitbox.y = self.hitbox_x, self.hitbox_y

    def update_pitch_default(self):
        speed_ratio = abs(self.speed / self.speed_cap)
        target_pitch = 0.5 + round(speed_ratio / 0.01) * 0.01
        if abs(target_pitch - self.last_pitch) > 0.01:  
            self.engine_player.pitch = target_pitch
            self.last_pitch = target_pitch

    def calculate_drift(self, dt):
        if self._cached_direction != self.direction:
            self._update_cached_trig()

        vel_angle = math.atan2(self.vel_y, self.vel_x)
        direction_rad = math.radians(self.direction)
        angle_diff = math.degrees((vel_angle - direction_rad + math.pi) % (2 * math.pi) - math.pi)
        diff = abs(angle_diff)
        modded = 90 - abs(90 - diff)
        drift_factor = modded / 90
        self.drifting = drift_factor > 0.1 and self.speed > 200

        self.drift_turn_strength = self.turn_strength * (0.5 + drift_factor)

        ang_vel = math.atan2(self.vel_y, self.vel_x)
        ang_head = math.radians(self.direction)
        ang_diff = (ang_vel - ang_head + math.pi) % (2 * math.pi) - math.pi
        corr = drift_factor * self.friction * self.speed
        lat_ang = ang_head + (math.pi / 2 if ang_diff < 0 else -math.pi / 2)
        self.vel_x += math.cos(lat_ang) * corr * dt
        self.vel_y += math.sin(lat_ang) * corr * dt

        fade = drift_factor * 0.01 * (1 - self.speed / self.speed_cap)
        self.vel_x *= 1 - fade
        self.vel_y *= 1 - fade

        measured = math.hypot(self.vel_x, self.vel_y) / dt
        head_rad = math.radians(self.direction)
        proj = self.vel_x * math.cos(head_rad) + self.vel_y * math.sin(head_rad)
        self.speed = math.copysign(measured, proj)

    def get_hitbox_corners(self, fx=None, fy=None):
        if fx is None or fy is None:
            fx, fy = self.hitbox.x, self.hitbox.y

        hw, hh = self.hitbox.width / 2, self.hitbox.height / 2
        fhw, fhh = (self.hitbox.width + 160) / 2, hh
        theta = math.radians(-self.hitbox.rotation)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        def compute_corners(cx, cy, w, h):
            local_corners = [(-w, h), (w, h), (w, -h), (-w, -h)]
            return [
                (cx + dx * cos_t - dy * sin_t, cy + dx * sin_t + dy * cos_t)
                for dx, dy in local_corners
            ]

        corners = compute_corners(self.hitbox.x, self.hitbox.y, hw, hh)
        future_corners = compute_corners(fx, fy, fhw, fhh)
        return corners, future_corners

    def update_corners_states(self, corners, future_corners, track):
        corner_states = [0] * 4
        future_states = [0] * 4

        track_x, track_y = track.sprite.x, track.sprite.y

        for idx, ((x, y), (fx, fy), dot) in enumerate(zip(corners, future_corners, self.hitbox_corners)):
            world_x, world_y = x - track_x, y - track_y
            future_world_x, future_world_y = fx - track_x, fy - track_y

            dot.x, dot.y = x, y

            current_result = track.is_on_track(world_x, world_y)
            future_result = track.is_on_track(future_world_x, future_world_y)

            if current_result is True: corner_states[idx] = 0
            elif current_result in (1, 2, 4, 5): corner_states[idx] = current_result
            else: corner_states[idx] = 3

            if future_result is True: future_states[idx] = 0
            elif future_result in (1, 2, 4, 5): future_states[idx] = future_result
            else: future_states[idx] = 3

        return corner_states, future_states

    def update_hitbox_corners(self, track, dt):
        corners, future_corners = self.get_hitbox_corners()
        back_left, front_left, front_right, back_right = 0, 1, 2, 3
        corner_states, future_states = self.update_corners_states(corners, future_corners, track)
        
        if 2 not in corner_states:
            corner_states = [3 if s == 4 else s for s in corner_states]
        
        collision_detected = any(s == 3 for s in corner_states) and corner_states != [3, 3, 3, 3]

        if collision_detected:
            if self.collision_frames == 0 or (self.collision_frames % 20 == 0):
                self.collision.play()
            self.collision_frames += 1
            self._update_cached_trig()

            front_collision = corner_states[front_left] == 3 and corner_states[front_right] == 3
            rear_collision = corner_states[back_left] == 3 and corner_states[back_right] == 3

            if front_collision:
                self.speed = math.copysign(max(abs(self.speed) / 10, 30), -1)
                self.vel_x = self.speed * self._cached_cos * dt
                self.vel_y = self.speed * self._cached_sin * dt
            elif rear_collision:
                self.speed = math.copysign(max(abs(self.speed) / 10, 30), 1)
                self.vel_x = self.speed * self._cached_cos * dt
                self.vel_y = self.speed * self._cached_sin * dt
            elif corner_states[front_left] == 3: self._handle_corner_collision(front_left, front_right, future_states, dt, -1)
            elif corner_states[front_right] == 3: self._handle_corner_collision(front_right, front_left, future_states, dt, 1)
            elif corner_states[back_left] == 3: self._handle_corner_collision(back_left, back_right, future_states, dt, 1, is_rear=True)
            elif corner_states[back_right] == 3: self._handle_corner_collision(back_right, back_left, future_states, dt, -1, is_rear=True)


        # Check for start(value 1)
        if any(state == 1 for state in corner_states):
            if not self.lap_started:
                self.lap_started = True
                self.checkpoint_reached = False 
                self.timer = 0
                print("Lap timer started!")

        # Check for checkpoint (value 5)
        elif any(state == 5 for state in corner_states):
            if self.lap_started:  
                self.checkpoint_reached = True
                print("Checkpoint reached!")

        # Check for finish (value 2)
        elif any(state == 2 for state in corner_states):
            if self.lap_started and self.checkpoint_reached and self.timer > 1:
                self.is_lap_finished = True
                self.lap_started = False  
                self.checkpoint_reached = False 
                print("Lap finished!")


    def _handle_corner_collision(self, primary_corner, secondary_corner, future_states, dt, spin_direction, is_rear=False):
        impact_factor = abs(self.speed / self.speed_cap)
        spin_impulse = spin_direction * self.collision_spin_force * impact_factor
        if is_rear:
            push_angle_offset = 45 * -spin_direction
        else:
            push_angle_offset = 160 * spin_direction

        push_angle_rad = math.radians(self.direction + push_angle_offset)

        if future_states[primary_corner] == 3 and future_states[secondary_corner] == 3:
            self.angular_velocity = spin_impulse * impact_factor * 45 * -1
            push_magnitude = self.collision_push_force * impact_factor
            if self.crashed: push_magnitude /= 20
            if impact_factor > 0.7: self.crashed = True
        else:
            self.angular_velocity += spin_impulse
            push_magnitude = self.collision_push_force * impact_factor
        push_force_x = math.cos(push_angle_rad) * push_magnitude * dt
        push_force_y = math.sin(push_angle_rad) * push_magnitude * dt
        self.vel_x += push_force_x
        self.vel_y += push_force_y
    def get_trail_pos(self):
        corners, _ = self.get_hitbox_corners()
        return [corners[0], corners[3]]

