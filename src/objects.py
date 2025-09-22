import pyglet
import static_object
import math
import time


class Track(static_object.StaticObject):
    # 210 -> 1 -> Start Line
    # 220 -> 2 -> Finish Line
    # 230 -> 5 -> Checkpoint 
    grayscale_markings = {255: True, 210: 1, 220: 2, 200: 3, 27: 4, 230: 5}

    def __init__(
        self,
        color_img,
        mask_img,
        window,
        scale=7,
        batch=None,
        group=pyglet.graphics.Group(2),
    ):
        self.group = group
        super().__init__(
            color_img, window, x=0, y=0, scale=scale, batch=batch, group=self.group
        )
        mask_sprite = pyglet.sprite.Sprite(mask_img, 0, 0)
        self.mask_width = mask_sprite.width
        self.mask_height = mask_sprite.height
        self.scaled_size=self.get_scaled_size()
        raw_data = mask_sprite.image.get_image_data()
        self.pixels = raw_data.get_bytes(fmt="L", pitch=self.mask_width)

    def get_scaled_size(self):
        return self.sprite.width, self.sprite.height

    def is_on_track(self, world_x, world_y):
        x = int(world_x / self.sprite.scale)
        y = int(world_y / self.sprite.scale)

        if x < 0 or y < 0 or x >= self.mask_width or y >= self.mask_height:
            return False

        try:
            idx = y * self.mask_width + x
            pixel = self.pixels[idx]
            return Track.grayscale_markings.get(pixel, False)
        except (IndexError, KeyError):
            return False


class Tree(static_object.StaticObject):
    def __init__(self, img, window, x=None, y=None, scale=1.0, batch=None, group=None):
        img.anchor_x = img.width / 2
        self.group = pyglet.graphics.Group(7)
        super().__init__(img, window, x, y, scale, batch, self.group)
        self.is_visible = False



class Trail:
    def __init__(self, batch):
        self.group = pyglet.graphics.Group(3)
        self.max_trail_size = 500
        self.lifetime = 2.0  # seconds before trail disappears

        self.trail = [
            pyglet.shapes.Circle(
                0, 0, 10, color=(50, 50, 50), batch=batch, group=self.group
            )
            for _ in range(self.max_trail_size)
        ]

        self.active_trails = set()
        self.trail_age = [self.lifetime] * self.max_trail_size
        self.trail_index = 0

        self._last_update_time = time.time()

    def update(self, dx, dy, car):
        current_time = time.time()
        dt = current_time - self._last_update_time
        self._last_update_time = current_time

        for i in list(self.active_trails):
            self.trail[i].x -= dx
            self.trail[i].y -= dy

            self.trail_age[i] += dt

            if self.trail_age[i] < self.lifetime:
                t = self.trail_age[i] / self.lifetime
                self.trail[i].opacity = int(255 * (1 - t))
                self.trail[i].radius = 10 * (1 - t)
            else:
                self.trail[i].opacity = 0
                self.trail[i].radius = 0
                self.active_trails.remove(i)

        if car.drifting:
            trail_positions = car.get_trail_pos()
            for corner in trail_positions:
                circle = self.trail[self.trail_index]
                circle.x = int(corner[0])
                circle.y = int(corner[1])
                circle.rotation = car.hitbox.rotation

                self.trail_age[self.trail_index] = 0.0
                self.active_trails.add(self.trail_index)
                self.trail_index = (self.trail_index + 1) % self.max_trail_size

