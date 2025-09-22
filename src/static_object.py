import pyglet


class StaticObject:
    def __init__(self, img, window, x=0, y=0, scale=1.0, batch=None, group=None):
        self.window = window
        self.batch=batch
        self.sprite = pyglet.sprite.Sprite(img, batch=batch, group=group)
        self.sprite.scale = scale

        # Default to center of screen if x or y is None

        self.sprite.x = x
        self.sprite.y = y

    def update(self, dx, dy):
        self.sprite.x -= dx
        self.sprite.y -= dy
