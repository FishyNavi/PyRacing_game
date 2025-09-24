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


def load_map(assets, i):
    all_map_data = load_sprite_data(1)
    map_names = list(all_map_data)
    name = map_names[i]
    
    map_properties = all_map_data[name]
    color_key = f"{name}_map"
    grayscale_key = f"{name}_map_grayscale"
    decorations_key = f"{name}_map_decorations"

    to_add_map = {
        "color_img": assets[color_key],
        "grayscale_img": assets[grayscale_key],
        "scale": map_properties["scale"],
        "spawn_point": map_properties["spawn_point"],
        "total_laps": map_properties["total_laps"],
    }
    if decorations_key in assets:
        to_add_map["decorations_img"] = assets[decorations_key]
    else:
        to_add_map["decorations_img"] = assets["tree"]
    return to_add_map


def load_car(assets, i):
    data = load_sprite_data(0)
    
    car_name = list(data)[i]
    car_properties = data[car_name]
    texture_key = f"{car_name}_texture"
    if texture_key in assets:
        output = {
                    "texture": assets[texture_key],
                    "power": car_properties["power"],
                    "friction": car_properties["friction"],
                    "scale": car_properties["scale"],
                }
        return output


def load_assets(asset_keys): # optimise tis for faster loading
    assets_path = os.path.join(getattr(sys, '_MEIPASS', os.getcwd()), "Assets")
    pyglet.resource.path = [assets_path]
    pyglet.resource.reindex()

    assets = {}
    for key in asset_keys:
        filename = f"{key}.png"
        try:
            assets[key] = pyglet.resource.image(filename)
        except Exception as e:
            print(f"Warning: Failed to load asset {filename}: {e}")
            assets[key] = None
    return assets

def init_menu(game,menu_img):
    button_configs = get_button_configs()
    labels = []
    for i in range(1, 11):
        labels.append({"text": f"Lap {i}: 0.00", "x": 50, "y": 40 * i, "lap": i})

    main_menu = Menu(game, button_configs, lap_labels=labels,menu_img=menu_img)
    return main_menu

def get_button_configs():
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
    def __init__(self, x, y, w, h, assets=None):
        self.visible = True
        self.background = pyglet.shapes.Rectangle(x/2-w/2,y/2-h/2, w, h, color=(241, 241, 241))
        self.image = None # We dont want to load assets each time
        if assets and "blohai" in assets:
            image=assets["blohai"]
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

def load_menu_img(assets):
    if "neco" in assets and assets["neco"]:
        img=assets["neco"]
        menu_sprite=pyglet.sprite.Sprite(img,0,0)
        return menu_sprite
    return None
