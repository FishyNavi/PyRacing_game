import math

class CollisionHandler:
    def __init__(self, car, track):
        self.car = car
        self.track = track

    def update(self, dt):
        car = self.car
        track = self.track

        corners, future_corners = car.get_hitbox_corners()
        corner_states, future_states = car.update_corners_states(corners, future_corners, track)
        
        if not car.checkpoint_reached:
             corner_states = [s if s != 2 else 3 for s in corner_states]

        if not car.lap_started:
             corner_states = [s if s != 5 else 3 for s in corner_states]

        collision_detected = any(s == 3 for s in corner_states)
        
        correction_x, correction_y = 0.0, 0.0
        if collision_detected:
            inside_wall_indices = [i for i, state in enumerate(corner_states) if state == 3]
            for idx in inside_wall_indices:
                corner_x, corner_y = corners[idx]
                dx = corner_x - car.hitbox.x
                dy = corner_y - car.hitbox.y
                correction_x -= dx
                correction_y -= dy

            mag = math.hypot(correction_x, correction_y)
            if mag > 0:
                push_strength = 2
                correction_x = (correction_x / mag) * push_strength
                correction_y = (correction_y / mag) * push_strength
        
        lerp_factor = 0.4 
        car.collision_correction_x = (1 - lerp_factor) * car.collision_correction_x + lerp_factor * correction_x
        car.collision_correction_y = (1 - lerp_factor) * car.collision_correction_y + lerp_factor * correction_y
        
        if collision_detected and corner_states != [3, 3, 3, 3]:
            if car.collision_frames == 0 or (car.collision_frames % 20 == 0):
                if car.collision:
                    car.collision.play()
            car.collision_frames += 1
            car._update_cached_trig()

            back_left, front_left, front_right, back_right = 0, 1, 2, 3
            front_collision = corner_states[front_left] == 3 and corner_states[front_right] == 3
            rear_collision = corner_states[back_left] == 3 and corner_states[back_right] == 3

            if front_collision:
                car.speed = math.copysign(max(round(abs(car.speed) ,-10)/ 10, 0.1), -1)
                print(max(round(abs(car.speed) ,-100)/ 10, 1), -1)
                car.vel_x = car.speed * car._cached_cos * dt
                car.vel_y = car.speed * car._cached_sin * dt
            elif rear_collision:
                car.speed = math.copysign(max(round(abs(car.speed) ,-10)/ 10, 0.1), 1)
                car.vel_x = car.speed * car._cached_cos * dt
                car.vel_y = car.speed * car._cached_sin * dt
            elif corner_states[front_left] == 3: self._handle_corner_collision(front_left, front_right, future_states, dt, -1)
            elif corner_states[front_right] == 3: self._handle_corner_collision(front_right, front_left, future_states, dt, 1)
            elif corner_states[back_left] == 3: self._handle_corner_collision(back_left, back_right, future_states, dt, 1, is_rear=True)
            elif corner_states[back_right] == 3: self._handle_corner_collision(back_right, back_left, future_states, dt, -1, is_rear=True)

        else:
            car.collision_frames = 0
            car.collision_correction_x *= 0.75
            car.collision_correction_y *= 0.75
            if abs(car.collision_correction_x) < 0.01: car.collision_correction_x = 0
            if abs(car.collision_correction_y) < 0.01: car.collision_correction_y = 0

        if any(state == 1 for state in corner_states):
            if not car.lap_started:
                car.lap_started = True
                car.checkpoint_reached = False 
                car.timer = 0
                print("Lap timer started!")

        elif any(state == 5 for state in corner_states):
            if car.lap_started:  
                car.checkpoint_reached = True
                print("Checkpoint reached!")

        elif any(state == 2 for state in corner_states):
            if car.lap_started and car.checkpoint_reached and car.timer > 1:
                car.is_lap_finished = True
                car.lap_started = False  
                car.checkpoint_reached = False 
                print("Lap finished!")

    def _handle_corner_collision(self, primary_corner, secondary_corner, future_states, dt, spin_direction, is_rear=False):
        car = self.car
        impact_factor = abs(car.speed / car.speed_cap)
        spin_impulse = spin_direction * car.collision_spin_force * impact_factor
        if is_rear:
            push_angle_offset = 45 * -spin_direction
        else:
            push_angle_offset = 160 * spin_direction

        push_angle_rad = math.radians(car.direction + push_angle_offset)

        if future_states[primary_corner] == 3 and future_states[secondary_corner] == 3:
            car.angular_velocity = spin_impulse * impact_factor * 45 * -1
            push_magnitude = car.collision_push_force * impact_factor
            if car.crashed: push_magnitude /= 20
            if impact_factor > 0.7: car.crashed = True
        else:
            car.angular_velocity += spin_impulse
            push_magnitude = car.collision_push_force * impact_factor
        push_force_x = math.cos(push_angle_rad) * push_magnitude * dt
        push_force_y = math.sin(push_angle_rad) * push_magnitude * dt
        car.vel_x += push_force_x
        car.vel_y += push_force_y

