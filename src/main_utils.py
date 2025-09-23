from ast import literal_eval
import os
import sys
import pyglet
from menu import Menu

def load_scores():
    filepath = "score.txt"
    default_scores = "[[], [], [], []]"

    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                return literal_eval(content)
        else:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(default_scores)
            return literal_eval(default_scores)

    except (ValueError, SyntaxError) as e:
        print(f"Error loading scores: {e}. Resetting score file.")
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(default_scores)
        return literal_eval(default_scores)


def load_sprite_data(i):
    if i == 0:
        return {
            "car": {"power": 100, "friction": 0.05, "scale": 4.5},
            "blue_car": {"power": 150, "friction": 0.1, "scale": 2.25},
            "car3": {"power": 100, "friction": 0.7, "scale": 1.1},
            "car4": {"power": 135, "friction": 0.55, "scale": 1.05},
        }
    elif i == 1:
        return {
            "track": {
                "scale": 7,
                "spawn_point": (6000, 1100),
                "total_laps": 1,
            },
            "trees_at_qatar": {
                "scale": 5,
                "spawn_point": (3200, 1700),
                "total_laps": 5,
            },
            "trees_at_batangas": {
                "scale": 7,
                "spawn_point": (6000, 4800),
                "total_laps": 7,
            },
            "donut": {"scale": 3, "spawn_point": (5000, 1000), "total_laps": 10},
        }


def load_map(assets,i):
    """
    Loads map data based on a list of map names, including a unique scale and spawn point for each.

    Returns:
        list: A list of dictionaries, where each dictionary represents a loaded map.
                If a map cannot be loaded, its corresponding entry in the list is None.
    """
    maps = []

    # Define unique properties for each map, including its scale and spawn point
    all_map_data = load_sprite_data(1)
    map_names = list(all_map_data)

    for name in map_names:
        color_key = f"{name}_map"
        grayscale_key = f"{name}_map_grayscale"
        decorations_key = f"{name}_map_decorations"

        # Check if map data exists and all required assets are present
        if name in all_map_data and all(
            key in assets for key in [color_key, grayscale_key]
        ):
            map_properties = all_map_data[name]
            to_add_map = {
                "color_img": assets[color_key],
                "grayscale_img": assets[grayscale_key],
                "scale": map_properties["scale"],
                "spawn_point": map_properties[
                    "spawn_point"
                ],
                "total_laps": map_properties["total_laps"],
            }
            if decorations_key in assets:
                to_add_map["decorations_img"] = assets[decorations_key]
            else:
                print(
                    f"No decoration image for map {name}. Tree image loaded instead"
                )
                to_add_map["decorations_img"] = assets["tree"]
            maps.append(to_add_map)
        else:
            print(
                f"Warning: Missing assets or data for map '{name}'. It will be unavailable."
            )
            maps.append(None)  # Placeholder
    return maps[i]


def load_car(assets,i):
    """
    Loads car data based on a list of car names, including unique power, friction, and scale.

    Args:
        car_names (list): A list of strings, where each string is the name of a car texture to load.

    Returns:
        list: A list of dictionaries, where each dictionary represents a loaded car.
                If a car cannot be loaded, its corresponding entry in the list is None.
    """
#    cars = []
    data = load_sprite_data(0)
    
    car_name = list(data)[i]
    car_properties = data[car_name]
    if f"{car_name}_texture" in assets:
        output = {
                    "texture": assets[f"{car_name}_texture"],
                    "power": car_properties["power"],
                    "friction": car_properties["friction"],
                    "scale": car_properties["scale"],
                }
        return output



#    for name in car_names:
#        if name in all_car_data and f"{name}_texture" in assets:
#            car_properties = all_car_data[name]
#            to_add_car = {
#                "texture": assets[f"{name}_texture"],
#                "power": car_properties["power"],
#                "friction": car_properties["friction"],
#                "scale": car_properties["scale"],
#            }
#            cars.append(to_add_car)
#        else:
#            
#            print(
#                f"Warning: Missing texture asset or data for car '{f"{name}_texture"}'."
#            )
#            cars.append(None)  # Placeholder

    


def load_assets():
    """Dynamically load all PNG assets from the Assets folder."""
    assets_path = os.path.join(getattr(sys, '_MEIPASS', os.getcwd()), "Assets")
    pyglet.resource.path = [assets_path]
    pyglet.resource.reindex()

    assets = {}
    try:
        for filename in os.listdir(assets_path):
            if filename.lower().endswith(".png"):
                key = os.path.splitext(filename)[0]
                try:
                    assets[key] = pyglet.resource.image(filename)
                except KeyError as e:
                    print(f"Warning: Failed to load asset {filename}: {e}")
                    assets[key] = None
    except KeyError as e:
        print(f"Error accessing assets directory: {e}")

    return assets
def init_menu(game,menu_img):
    button_configs = get_button_configs()
    #
    #        play_button = {
    #            "unpressed": self.assets["play_unpressed"],
    #            "pressed": self.assets["play_pressed"],
    #            "hover": self.assets["play_hover"],
    #            "x": 50,
    #            "y": self.window.height / 3 * 2,
    #        }
    #        settings_button = {
    #            "unpressed": self.assets["settings_unpressed"],
    #            "pressed": self.assets["settings_pressed"],
    #            "hover": self.assets["settings_hover"],
    #            "x": 50,
    #            "y": self.window.height / 3 * 2 - 60,
    #        }
    #        continue_button = {
    #            "unpressed": self.assets["continue_unpressed"],
    #            "pressed": self.assets["continue_pressed"],
    #            "hover": self.assets["continue_hover"],
    #            "x": 50,
    #            "y": self.window.height / 3 * 2,
    #        }
    #        # exit_button={"unpressed":self.assets["exit_unpressed"],"pressed":self.assets["exit_pressed"],"hover":self.assets["exit_hover"],"x":50,"y":self.window.height/3*2+70}
    #        # restart_button={"unpressed":self.assets["restart_unpressed"],"pressed":self.assets["restart_pressed"],"hover":self.assets["restart_hover"],"x":50,"y":self.window.height/3*2+140}

    #        self.main_menu = Menu(
    #            play_button=play_button,
    #            settings_button=settings_button,
    #            continue_button=continue_button,
    #            lap_labels=labels,
    #        )  # ,exit_button=exit_button
    #        self.push_button_handlers()

    labels = []
    for i in range(1, 11):

        labels.append({"text": f"Lap {i}: 0.00", "x": 50, "y": 40 * i, "lap": i})

    main_menu = Menu(game, button_configs, lap_labels=labels,menu_img=menu_img)
    return main_menu

def get_button_configs():
    """Returns a dictionary of configurations for all buttons with distinct colors."""

    green_scheme = {
        "normal": (10, 80, 50, 255),  
        "hover": (50, 160, 100, 255), 
        "press": (0, 50, 30, 255),  
        "disabled": (60, 100, 80, 150), 
    }

    blue_scheme = {
        "normal": (40, 10, 80, 255),  
        "hover": (100, 80, 200, 255),  
        "press": (20, 5, 60, 255), 
        "disabled": (60, 40, 120, 150),  
    }

    red_scheme = {
        "normal": (80, 10, 50, 255),  
        "hover": (200, 80, 100, 255),  
        "press": (50, 0, 20, 255),  
        "disabled": (120, 60, 80, 150),  
    }

    configs = {
        "main": [
            {
                "text": "Play",
                "x": 20,
                "y": 400,
                "width": 200,
                "height": 40,
                "colors": blue_scheme,
            },
            {
                "text": "Settings",
                "x": 20,
                "y": 340,
                "width": 200,
                "height": 40,
                "colors": blue_scheme,
            },
            {
                "text": "Exit",
                "x": 20,
                "y": 280,
                "width": 200,
                "height": 40,
                "colors": red_scheme,
            },
            {
                "text": "Continue",
                "x": 20,
                "y": 400,
                "width": 200,
                "height": 40,
                "colors": blue_scheme,
            },
            {
                "text": "Restart",
                "x": 20,
                "y": 160,
                "width": 200,
                "height": 40,
                "colors": blue_scheme,
            },
        ],
        "maps": [
            {
                "text": f"Map {i+1}",
                "x": 20,
                "y": 400 - i * 50,
                "width": 180,
                "height": 40,
                "colors": green_scheme,
            }
            for i in range(4)
        ],
        "cars": [
            {
                "text": f"Car {i+1}",
                "x": 20,
                "y": 400- i * 50,
                "width": 180,
                "height": 40,
                "colors": green_scheme,
            }
            for i in range(4)
        ],
    }
    return configs

class Popup:
    def __init__(self, x, y, w, h,image=None):
        
        
        self.visible = True
        self.background = pyglet.shapes.Rectangle(x/2-w/2,y/2-h/2, w, h, color=(241, 241, 241))
        if image:
            temp=load_assets()
            image=temp["blohai"]
            self.image=pyglet.sprite.Sprite(image,x/2-image.width*0.4/2,y/2-image.height*0.4/2)
            
            self.image.scale=0.4

        self.label = pyglet.text.Label(
            "Probably not what you expected :3. Press e to close.",
            x=self.background.x + w // 2,
            y=self.background.y+20,
            anchor_x="center",
            anchor_y="center",
            color=(50, 50, 50),
        )
        

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def draw(self):
        if self.visible:
            self.background.draw()
            self.label.draw()
            if self.image:
                self.image.draw()
def load_menu_img():
    assets=load_assets()
    if "neco" in assets:
        img=assets["neco"]
        menu_sprite=pyglet.sprite.Sprite(img,0,0)
        return menu_sprite
    
    