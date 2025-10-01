import pyglet
from pyglet.window import key
from objects import Track, Trail
import objects
from tree_manager import TreeManager

class GameWorld:
    """
    Manages all the objects that make up the game world.
    This includes the track, decorations, and trees.
    """
    def __init__(self, window, batch, map_data, assets):
        map_scale = map_data["scale"]

        self.track = Track(
            map_data["color_img"],
            map_data["grayscale_img"],
            window,
            scale=map_scale,
            batch=batch,
        )

        self.decorations = objects.static_object.StaticObject(
            map_data["decorations_img"],
            window,
            scale=map_scale,
            batch=batch,
            group=pyglet.graphics.Group(6),
        )

        self.tree_manager = TreeManager(
            image=assets["tree"],
            window=window,
            scale=map_scale,
            world_width=self.track.scaled_size[0],
            world_height=self.track.scaled_size[1],
            batch=batch,
        )
        self.tree_manager.generate_trees(1000, self.track)

        self.trail = Trail(batch=batch)

    def update(self, dx, dy, car=None):
        """Updates the position of all world objects."""
        self.track.update(dx, dy)
        self.decorations.update(dx, dy)
        self.tree_manager.update(dx, dy, None) 
        if car:
            self.trail.update(dx, dy, car)

    def cleanup(self):
        """Prepares world objects for deletion."""
        self.track = None
        self.decorations = None
        self.tree_manager = None
        self.trail = None


class RaceManager:
    """
    Manages the state and rules of the race, like laps, timing, and crashes.
    """
    def __init__(self, game_instance, car):
        self.game = game_instance
        self.car = car
        self.time_after_crash = 0
        self.is_race_finished = False
        self.current_lap = 1
        self.total_laps = 0
        self.spawn_point = (0, 0)

    def start_race(self, laps, spawn_point):
        """Initializes the race parameters."""
        self.total_laps = laps
        self.spawn_point = spawn_point
        self.current_lap = 1
        self.is_race_finished = False

    def update(self, dt):
        """Handles race logic each frame."""
        if self.car.is_lap_finished:
            self.current_lap += 1
            self.car.timer = 0
            self.car.is_lap_finished = False
            if self.current_lap > self.total_laps:
                total_time = self.game.main_menu.count_total_time()
                self.is_race_finished = True
                self.game.add_score(total_time[0], total_time[1])

        self.car.timer += dt
        self.game.lap_time = self.car.timer # UI label

        if self.car.crashed:
            self.handle_crash(dt)

    def handle_crash(self, dt):
        """Manages the logic for when the car has crashed."""
        self.time_after_crash += dt
        self.car.vel_x *= 0.92
        self.car.vel_y *= 0.92
        if self.car.update_pitch:
            self.car.engine_player.pitch = 0.3

        if self.time_after_crash > 5:
            self.time_after_crash = 0
            self.car.crashed = False
            self.car.drifting = False
            self.game.teleport_car_to_pos(self.spawn_point[0], self.spawn_point[1], -180)
            self.car.timer = 0


class InputHandler:
    """
    Handles global keyboard inputs like pause, reset, and freecam.
    """
    def __init__(self, game_instance, keys):
        self.game = game_instance
        self.keys = keys
        self.p_pressed_last = False
        self.r_pressed_last = False
        self.f_pressed_last = False
        self.e_pressed_last = False

    def update(self):
        """Checks for and acts on key presses."""
        p_pressed = self.keys[key.P]
        if p_pressed and not self.p_pressed_last and not self.game.is_on_menu:
            self.game.paused = True
        self.p_pressed_last = p_pressed

        r_pressed = self.keys[key.R]
        if r_pressed and not self.r_pressed_last:
#            self.game.cleanup_game_objects()
            self.game.is_on_menu = True
            self.game.paused = True
        self.r_pressed_last = r_pressed

        f_pressed = self.keys[key.F]
        if f_pressed and not self.f_pressed_last and self.game.car:
            self.game.car.is_freecam = not self.game.car.is_freecam
            self.game.teleport_camera_to_car()
        self.f_pressed_last = f_pressed

        e_pressed = self.keys[key.E]
        if e_pressed and not self.e_pressed_last:
            self.game.settings=False
        self.e_pressed_last = e_pressed
