import pyglet
from functools import partial
import sys

class LabelWithBackground:
    def __init__(
        self,
        text,
        x,
        y,
        padding=10,
        font_size=14,
        color=(255, 255, 255, 255),
        bg_color=(0, 0, 0, 128),
        batch=None,
        min_width=50,
    ):
        self.padding = padding
        self.min_width = min_width
        self.visible = True
        self.batch = batch
        self.x = x
        self.y = y

        self.label = pyglet.text.Label(
            text, x=x, y=y, font_size=font_size, color=color, batch=batch
        )

        text_width = self.label.content_width
        text_height = self.label.content_height
        self.bg_width = max(text_width + 2 * self.padding, self.min_width)
        self.bg_height = text_height + self.padding
        self.target_bg_width = self.bg_width

        self.background = pyglet.shapes.Rectangle(
            x=self.x - padding,
            y=self.y - padding,
            width=self.bg_width,
            height=self.bg_height,
            color=bg_color[:3],
            batch=batch,
        )
        self.background.opacity = bg_color[3]

        self.animation_speed = 200

    def _update_background_position(self):
        self.background.x = self.x - self.padding
        self.background.y = self.y - self.padding
        self.label.x = self.x
        self.label.y = self.y

    def set_text(self, text):
        self.label.text = text
        new_width = round((self.label.content_width + 2 * self.padding) / 10) * 10
        new_width = max(new_width, self.min_width) 

        if abs(new_width - self.target_bg_width) > 10:
            self.target_bg_width = new_width

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self._update_background_position()

    def hide(self):
        if self.visible:
            self.visible = False
            r, g, b, _ = self.label.color
            self.label.color = (r, g, b, 0)
            self.background.opacity = 0

    def show(self):
        if not self.visible:
            self.visible = True
            r, g, b, _ = self.label.color
            self.label.color = (r, g, b, 255)
            self.background.opacity = 128

    def update(self, dt):
        if abs(self.bg_width - self.target_bg_width) > 1:
            diff = self.target_bg_width - self.bg_width
            step = self.animation_speed * dt
            if abs(diff) < step:
                self.bg_width = self.target_bg_width
            else:
                self.bg_width += step if diff > 0 else -step

            self.bg_width = max(self.bg_width, self.min_width)
            self.background.width = self.bg_width
            self._update_background_position()

    @property
    def text(self):
        return self.label.text

    @text.setter
    def text(self, value):
        self.set_text(value)


class TextButton:
    """A button rendered with a text label and a colored rectangle."""

    def __init__(self, text, x, y, width, height, colors, batch, group=None):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.colors = colors
        self.target_color = (0, 0, 0, 0)
        self.on_press = lambda *args: None


        self._enabled = True
        self._is_hovered = False
        self._is_pressed = False

        self.rect = pyglet.shapes.BorderedRectangle(
            x,
            y,
            width,
            height,
            color=colors["normal"][:3],
            border_color=(255, 255, 255),
            batch=batch,
            group=group,
        )
        self.label = pyglet.text.Label(
            text,
            x=x + width / 2,
            y=y + height / 2,
            anchor_x="center",
            anchor_y="center",
            batch=batch,
            group=group,
        )
    
    def _check_bounds(self, x, y):
        return (x, y) in self.rect

    def update_visuals(self):
        if not self._enabled:
            color = self.colors["disabled"]
        elif self._is_pressed:
            color = self.colors["press"]
        elif self._is_hovered:
            color = self.colors["hover"]
        else:
            color = self.colors["normal"]

        self.target_color = tuple(color[:3]) + (color[3] if len(color) > 3 else 255,)

        self.label.color = (255, 255, 255, self.rect.opacity)
        self.rect.color = tuple(
            int(c + (t - c) / 10) for t, c in zip(self.target_color, self.rect.color)
        )

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if self._enabled != value:
            self._enabled = value

    @property
    def visible(self):
        return self.rect.visible

    @visible.setter
    def visible(self, value):
        self.rect.visible = value
        self.label.visible = value

    def handle_mouse_motion(self, x, y):
        if not self.visible or not self._enabled:
            return
        self._is_hovered = self._check_bounds(x, y)

    def handle_mouse_press(self, x, y):
        if not self.visible or not self._enabled or not self._is_hovered:
            return
        self._is_pressed = True

    def handle_mouse_release(self, x, y):
        if not self.visible or not self._enabled or not self._is_pressed:
            return
        was_pressed = self._is_pressed
        self._is_pressed = False
        if was_pressed and self._check_bounds(x, y):
            self.on_press()

    def delete(self):
        self.rect.delete()
        self.label.delete()


class ButtonManager:
    """Manages the creation, storage, and event dispatching for TextButtons."""

    def __init__(self, batch):
        self.batch = batch
        self.all_buttons = []
        self.main_buttons = []
        self.map_pick_buttons = []
        self.car_pick_buttons = []

    def _create_button(self, config):
        if not config:
            return None
        button = TextButton(
            text=config["text"],
            x=config["x"],
            y=config["y"],
            width=config["width"],
            height=config["height"],
            colors=config["colors"],
            batch=self.batch,
        )
        self.all_buttons.append(button)
        return button

    def init_main_buttons(self, buttons_data):
        for config in buttons_data:
            btn = self._create_button(config)
            self.main_buttons.append(btn)

    def init_map_pick_buttons(self, maps_data):
        for config in maps_data:
            btn = self._create_button(config)
            self.map_pick_buttons.append(btn)

    def init_car_pick_buttons(self, cars_data):
        for config in cars_data:
            btn = self._create_button(config)
            self.car_pick_buttons.append(btn)

    def update_visibility(self):
        for button in self.all_buttons:
            if button:
                button.visible = button.enabled

    def update_buttons(self):
        for button in self.all_buttons:
            button.update_visuals()

    def dispatch_mouse_motion(self, x, y, dx, dy):
        for button in self.all_buttons:
            button.handle_mouse_motion(x, y)

    def dispatch_mouse_press(self, x, y, button, modifiers):
        for btn in self.all_buttons:
            btn.handle_mouse_press(x, y)

    def dispatch_mouse_release(self, x, y, button, modifiers):
        for btn in self.all_buttons:
            btn.handle_mouse_release(x, y)


class Menu:
    def __init__(self, game, button_configs, lap_labels=None, menu_img=None):
        self.game = game
        self.picking_map = False
        self.picking_car = False
        self.map_selected = None
        self.car_selected = None

        self.batch = pyglet.graphics.Batch()

        self.menu_img=menu_img
        self.menu_img.batch=self.batch

        self.button_manager = ButtonManager(self.batch)
        self.button_manager.init_main_buttons(button_configs["main"])
        self.button_manager.init_map_pick_buttons(button_configs["maps"])
        self.button_manager.init_car_pick_buttons(button_configs["cars"])

        self.labels_data = list(lap_labels) if lap_labels else []
        self.labels = []
        self.best_time_label = None
        self._init_labels()
        self._assign_button_callbacks()

    def _init_labels(self):
        for label_data in self.labels_data:
            if label_data:
                label = LabelWithBackground(
                    text=label_data["text"],
                    x=label_data["x"],
                    y=label_data["y"],
                    padding=8,
                    font_size=14,
                    color=(255, 255, 255, 255),
                    bg_color=(0, 0, 0, 128),
                    batch=self.batch,
                    min_width=150,
                )
                self.labels.append(label)

        # ### CHANGED ###: Initialize the best time label
        self.best_time_label = LabelWithBackground(
            text="Best Time: N/A",
            x=220,
            y=400,
            font_size=16,
            batch=self.batch,
            min_width=200
        )
        self.best_time_label.hide() # Initially hidden

    def _assign_button_callbacks(self):
        bm = self.button_manager
        if bm.main_buttons[0]:
            bm.main_buttons[0].on_press = self.game_start
        if bm.main_buttons[1]:
            bm.main_buttons[1].on_press = self.settings
        if bm.main_buttons[2]:
            bm.main_buttons[2].on_press = self.exit_menu
        if bm.main_buttons[3]:
            bm.main_buttons[3].on_press = self.continue_game


        for i, button in enumerate(bm.map_pick_buttons):
            if button:
                button.on_press = partial(self.on_map_pick, i)

        for i, button in enumerate(bm.car_pick_buttons):
            if button:
                button.on_press = partial(self.on_car_pick, i)

    def update(self, dt):
        is_main_menu_active = (
            self.game.is_on_menu and not self.picking_map and not self.picking_car
        )
        is_paused_active = (
            not self.game.is_on_menu
            and not self.picking_map
            and not self.picking_car
            and self.game.paused
        )
        is_game_finished = self.game.is_race_finished
        is_in_game = (
            not is_paused_active
            and not is_main_menu_active
            and not self.picking_car
            and not self.picking_map
        )

        bm = self.button_manager
        if bm.main_buttons[0]: bm.main_buttons[0].enabled = is_main_menu_active
        if bm.main_buttons[1]: bm.main_buttons[1].enabled = is_main_menu_active or is_paused_active
        if bm.main_buttons[2]: bm.main_buttons[2].enabled = is_main_menu_active or is_paused_active or is_game_finished
        if bm.main_buttons[3]: bm.main_buttons[3].enabled = is_paused_active
        if bm.main_buttons[4]: bm.main_buttons[4].enabled = is_game_finished

        for button in bm.map_pick_buttons:
            if button: button.enabled = self.picking_map
        for button in bm.car_pick_buttons:
            if button: button.enabled = self.picking_car

        bm.update_buttons()

 
        if self.picking_car:
            self.best_time_label.show()
        else:
            self.best_time_label.hide()
        self.best_time_label.update(dt)

        for label, data in zip(self.labels, self.labels_data):
            if not is_in_game:
                label.hide()
            else:
                if data["lap"] <= self.game.laps:
                    label.show()
                else:
                    label.hide()
                if data["lap"] == self.game.current_lap:
                    label.set_text(f"Lap {data['lap']}: {round(self.game.lap_time,2)}")
            label.update(dt)
        
        if self.menu_img: self.menu_img.visible=is_main_menu_active or self.picking_car or self.picking_map

    def draw(self):
        self.button_manager.update_visibility()
        self.batch.draw()
        
    def reset_labels(self):
        for label in self.labels:
            a=label.text.split(":")[0]
            b=": 0.00"
            label.text=a+b
            

    def on_map_pick(self, index):
        print(f"Map {index} selected")
        self.map_selected = index
        self.picking_map = False
        self.picking_car = True

        # Fetch and display the best time for this map
        
        best_time_data = self.game.score[index]
        if best_time_data:
            best_time = best_time_data[0]
            self.best_time_label.set_text(f"Best Time: {best_time:.2f}s")
        else:
            self.best_time_label.set_text("Best Time: N/A")


    def on_car_pick(self, index):
        print(f"Car {index} selected")
        self.car_selected = index
        if self.game.init_game():
            self.picking_car = False
            self.game.paused = False
            self.game.is_on_menu = False
        else:
            print("Initialization failed. Returning to map selection.")
            self.picking_car = False
            self.picking_map = True

    def game_start(self):
        self.picking_map = True
        self.game.is_on_menu = True
    def exit_menu(self):
        sys.exit()
    def settings(self):
        print("*settings opened*")
        self.game.settings=True

    def continue_game(self):
        self.game.paused = False

    def count_total_time(self):
        total_time = 0
        lap_times=[]
        for i, label in enumerate(self.labels):
            if i < self.game.laps:
                try:
                    time_str = label.text.split(":")[1].strip()
                    time = float(time_str)
                    total_time += time
                    lap_times.append(time)
                except (IndexError, ValueError):
                    print(f"Could not parse time from label: {label.text}")
        return total_time, lap_times
