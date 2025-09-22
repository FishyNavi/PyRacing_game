import random
from objects import Tree
import pyglet


class TreeManager:
    def __init__(
        self,
        image,
        window,
        scale=1.0,
        world_width=1000,
        world_height=1000,
        batch=None,
    ):
        self.trees = []
        self.window = window
        self.image = image
        self.scale = scale
        self.world_width = world_width
        self.world_height = world_height
        self.batch = batch
        self.group = pyglet.graphics.Group(6)


        self.update_radius = 500
        self.last_car_pos = (0, 0)
        self.position_threshold = (
            50 
        )

    def generate_trees(self, amount, track):
        attempts = 0
        max_attempts = amount * 10 

        for _ in range(amount):
            if attempts > max_attempts:
                break

            x, y = None, None
            while attempts < max_attempts:
                x = random.randint(0, self.world_width)
                y = random.randint(0, self.world_height)
                attempts += 1

                if not track.is_on_track(x, y):
                    break

            # Create tree at world position, scaled to match track
            tree = Tree(
                self.image,
                self.window,
                x=x,
                y=y,
                scale=7,
                batch=self.batch,
                group=self.group,
            )
            self.trees.append(tree)

    def update(self, dx, dy, wdim):
        if dx != 0 or dy != 0:
            for tree in self.trees:
                tree.update(dx, dy)
               

   
        

    def get_all(self):
        return self.trees
