import pyglet
from pyglet.shapes import Rectangle
from pyglet.text import Label

class AnimatedButton:
    """
    A clickable button that animates its size on hover, rendered without images.
    
    The button's action is triggered on mouse release, which is standard UI practice.
    """
    def __init__(self, text, x, y, width, height, on_press,
                 text_color=(255, 255, 255, 255),
                 bg_color=(80, 80, 80, 255),
                 hover_color=(100, 100, 100, 255),
                 press_color=(60, 60, 60, 255),
                 batch=None, group=None):

        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.on_press = on_press

        self.colors = {
            'normal': bg_color,
            'hover': hover_color,
            'press': press_color
        }

        self._is_hovered = False
        self._is_pressed = False
        self.enabled = False

        # Animation parameters
        self._normal_scale = 1.0
        self._hover_scale = 1.05
        self._current_scale = self._normal_scale
        self._animation_speed = 7.0 

        self.background = Rectangle(x, y, width, height, color=bg_color[:3], batch=batch, group=group)
        self.background.opacity = bg_color[3]
        self.background.anchor_x = width / 2
        self.background.anchor_y = height / 2

        self.label = Label(text,
                           font_name='Arial',
                           font_size=height / 2.5,
                           x=x, y=y,
                           anchor_x='center', anchor_y='center',
                           color=text_color,
                           batch=batch, group=group)

    @property
    def bounding_box(self):
        """Returns the unscaled bounding box for consistent hit detection."""
        half_w = self.width / 2
        half_h = self.height / 2
        return (self.x - half_w, self.y - half_h, self.x + half_w, self.y + half_h)

    def update(self, dt):
        """Updates the button's animation and appearance each frame."""
        if not self.enabled:
            self._is_hovered = False

        target_scale = self._hover_scale if self._is_hovered else self._normal_scale

        self._current_scale += (target_scale - self._current_scale) * self._animation_speed * dt

        self.background.scale = self._current_scale
        self.label.scale = self._current_scale

        if self._is_pressed:
            current_color = self.colors['press']
        elif self._is_hovered:
            current_color = self.colors['hover']
        else:
            current_color = self.colors['normal']
        
        self.background.color = current_color[:3]
        self.background.opacity = current_color[3]

        self.background.visible = self.enabled
        self.label.visible = self.enabled

    def on_mouse_motion(self, x, y):
        """Checks if the mouse is hovering over the button."""
        if not self.enabled:
            self._is_hovered = False
            return
            
        l, b, r, t = self.bounding_box
        self._is_hovered = l < x < r and b < y < t

    def on_mouse_press(self, x, y, button):
        """Checks if the button was pressed."""
        if self.enabled and self._is_hovered and button == pyglet.window.mouse.LEFT:
            self._is_pressed = True

    def on_mouse_release(self, x, y, button):
        """Triggers the button's action if released while hovered."""
        if self.enabled and self._is_pressed and button == pyglet.window.mouse.LEFT:
            self._is_pressed = False
            l, b, r, t = self.bounding_box
            if l < x < r and b < y < t:
                if self.on_press:
                    self.on_press()