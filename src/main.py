import pyglet
import os
import sys
from pyglet.window import key, Window, FPSDisplay
from pyglet.gl import GL_NEAREST
from pyglet.image import Texture

from player import Car
from main_utils import *
from game_logic import GameWorld, RaceManager, InputHandler


# Tell opengl to not blur image
Texture.default_mag_filter = Texture.default_min_filter = GL_NEAREST


class Game:

    def __init__(self):
        self.window = Window(1280, 720, caption="Track Demo")
        
        self.menu_assets = load_assets(['neco', 'blohai'])
        self.game_assets = {}

        self.settings_popup=Popup(1280,720,400,650, self.menu_assets)
        menu_img_sprite=load_menu_img(self.menu_assets)
        if not menu_img_sprite:
            del menu_img_sprite
            
        self.fps = FPSDisplay(self.window)
        self.keys = key.KeyStateHandler()
        self.window.push_handlers(self.keys)
        
        # Game and UI State
        self.paused = True
        self.is_on_menu = True
        self.settings = False
        self.score = load_scores()

        # Core Components
        self.batch = pyglet.graphics.Batch()
        self.main_menu = init_menu(self, menu_img_sprite)
        self.input_handler = InputHandler(self, self.keys)

        # Game-specific objects (initialized later)
        self.car = None
        self.world = None
        self.race_manager = None
        
        # UI time label thingy
        self.lap_time = 0
        
        # Start the main game loop
        pyglet.clock.schedule_interval(self.game_update, 1 / 60.0)

        # Pyglet event handlers
        self.window.push_handlers(
            on_mouse_motion=self.main_menu.button_manager.dispatch_mouse_motion,
            on_mouse_press=self.main_menu.button_manager.dispatch_mouse_press,
            on_mouse_release=self.main_menu.button_manager.dispatch_mouse_release,
            on_draw=self.on_draw,
            on_close=self.on_close,
        )

    def game_update(self, dt):
        """The main game loop, called 60 times per second."""
        self.input_handler.update()
        self.main_menu.update(dt)

        if self.paused or self.is_on_menu:
            if self.car and self.car.engine_player:
                self.car.engine_player.pause()
            self.window.set_mouse_visible(True)
            return

        self.window.set_mouse_visible(False)
        if not self.car.engine_player.playing:
            self.car.engine_player.play()

        # Update all game logic
        self.car.update_hitbox_corners(self.world.track, dt)
        self.car.update(dt, self.keys)
        self.race_manager.update(dt)

        # Move the world based on the car's movement
        car_dx = self.car.smoothx + self.car.collision_correction_x
        car_dy = self.car.smoothy + self.car.collision_correction_y
        self.world.update(car_dx, car_dy, self.car)

    def init_game(self):
        """Initializes and sets up all objects for a new game session."""
        if self.car and self.car.engine_player:
            self.car.engine_player.pause()
            self.car.engine_player.delete()

        self.batch = pyglet.graphics.Batch() 
        self.world = None
        self.car = None
        self.race_manager = None

        map_index = self.main_menu.map_selected
        car_index = self.main_menu.car_selected

        # Reworked :D
        all_car_data = load_sprite_data(0) 
        car_name = list(all_car_data)[car_index]
        all_map_data = load_sprite_data(1)
        map_name = list(all_map_data)[map_index]

        required_assets = [
            f"{car_name}_texture",
            f"{map_name}_map",
            f"{map_name}_map_grayscale",
            "tree"
        ]
        
        decorations_key = f"{map_name}_map_decorations"
        assets_path = os.path.join(getattr(sys, '_MEIPASS', os.getcwd()), "Assets")
        if os.path.exists(os.path.join(assets_path, f"{decorations_key}.png")):
            required_assets.append(decorations_key)

        self.game_assets = load_assets(required_assets)

        map_data = load_map(self.game_assets, map_index)
        car_data = load_car(self.game_assets, car_index)
        
        if not map_data or not car_data:
            return False

        # Create the core game components
        self.world = GameWorld(self.window, self.batch, map_data, self.game_assets)
        self.car = Car(
            car_data["texture"], self.window, car_data["power"],
            car_data["friction"], car_data["scale"], batch=self.batch
        )
        self.race_manager = RaceManager(self, self.car)
        self.race_manager.start_race(map_data["total_laps"], map_data["spawn_point"])
        
        # Final setup
        self.main_menu.reset_labels()
        self.teleport_car_to_pos(
            self.race_manager.spawn_point[0], self.race_manager.spawn_point[1], -180
        )
        self.score = load_scores()
 
        # Workaround for my audio driver issues. 
        if os.name == 'posix':
            print("Nya")
                
            if isinstance(pyglet.media.get_audio_driver(), pyglet.media.drivers.pulse.adaptation.PulseAudioDriver):
                self.car.update_pitch = None
            
        return True

    def teleport_camera_to_car(self):
        """Moves the world so the car is in the center of the screen."""
        dx_world = self.car.hitbox.x - (self.window.width / 2)
        dy_world = self.car.hitbox.y - (self.window.height / 2)
        self.world.update(dx_world, dy_world, self.car)

    def teleport_car_to_pos(self, target_world_x, target_world_y, car_dir=None):
        """Moves the world to effectively 'teleport' the car to a new position."""
        # Some advanced math
        screen_center_x = self.window.width / 2
        screen_center_y = self.window.height / 2

        final_track_x = screen_center_x - target_world_x
        final_track_y = screen_center_y - target_world_y

        delta_move_x = final_track_x - self.world.track.sprite.x
        delta_move_y = final_track_y - self.world.track.sprite.y

        dx = -delta_move_x
        dy = -delta_move_y

        self.world.update(dx, dy, self.car)
        if car_dir:
            self.car.direction = car_dir
            
    def add_score(self, total_time, lap_times):
        """Add or update the score for the current map."""
        map_number = self.main_menu.map_selected

        while len(self.score) <= map_number:
            self.score.append([])

        existing_score = self.score[map_number]

        if not existing_score or total_time < existing_score[0]:
            self.score[map_number] = [total_time] + lap_times
            with open("score.txt", "w", encoding="utf-8") as f:
                f.write(str(self.score))


    def on_draw(self):
        """Draws all game objects."""
        self.window.clear()
        if not self.is_on_menu:
            self.batch.draw()
            self.fps.draw()
        self.main_menu.draw()
        if self.settings:
            self.settings_popup.draw()

    def on_close(self):
        """Cleans up resources when the window is closed."""
#        self.cleanup()             For some reason, when i was testing game, my ram was taken by something after some restarts. 
                                    # I thougth that its because of memory leaks or something and made a cleanup function. 
                                    # But this was not the problem because python releases all used memory when process is stopped. 
                                    # I guess it was just an coincidence, but ill keep cleanup in the code commented
        self.window.close()
        return True

#    def cleanup_game_objects(self):
#        """Cleans up game-related objects for a reset."""
#        if self.car:
#            if self.car.engine_player: self.car.engine_player.delete()
#            if self.car.collision_player: self.car.collision_player.delete()
#        
#        # Re-create the batch for a clean slate
#        self.batch = pyglet.graphics.Batch()
#
#        if self.world:
#            self.world.cleanup()
#            self.world = None
#        
#        self.car = None
#        self.race_manager = None

#    def cleanup(self):
#        """Proper resource cleanup to prevent memory leaks."""
#        try:
#            self.cleanup_game_objects()
#            if hasattr(self, "main_menu"):
#                for button in self.main_menu.button_manager.all_buttons:
#                    if button: button.delete()
#            self.window.remove_handlers()
#        except Exception as e:
#            print(f"Warning during cleanup: {e}")

    def run(self):
        """Runs the game and handles cleanup."""
        
        pyglet.app.run()
        



@property
def laps(self):
    return self.race_manager.total_laps if self.race_manager else 0

@property
def current_lap(self):
    return self.race_manager.current_lap if self.race_manager else 0

@property
def is_race_finished(self):
    return self.race_manager.is_race_finished if self.race_manager else False


Game.laps = laps
Game.current_lap = current_lap
Game.is_race_finished = is_race_finished


if __name__ == "__main__":
    game = Game()
    try:
        game.run()
    except KeyboardInterrupt:
        print("Game interrupted by user")
#    finally:
#        print("exit")
#        game.cleanup()

