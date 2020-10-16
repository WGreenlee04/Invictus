from math import floor
from typing import Tuple

import pyglet
from collision import collide, Response, Vector, Circle, Poly
from pyglet.window import key
from pyglet.window.key import KeyStateHandler

Cell = [int, int]


class KeyMap:
    defaults = {
        'up': key.W,
        'down': key.S,
        'left': key.A,
        'right': key.D
    }

    def __init__(self, up, down, left, right):
        self.up = up
        self.down = down
        self.left = left
        self.right = right


class Asset(pyglet.sprite.Sprite):
    """
    Anything that is drawn onto the screen that isn't an overlay.
    """

    def __init__(self, rel_pos_vector: Vector, window_width: int, window_height: int,
                 image_path: str = None, desired_width: float = None, desired_height: float = None, *args, **kwargs):
        """
        :param rel_pos_vector: relative position to the top left corner of the screen
        and bottom left corner of the screen as a Vector of type collisions.Vector.
        :param window_width: width of the window the Asset is in.
        :param window_height: height of the window the Asset is in.
        :param image_path: path to the image file from the pyglet search directory nearest it.
        """
        if image_path:
            img = pyglet.resource.image(image_path)
            img.anchor_x = img.width // 2
            img.anchor_y = img.height // 2
        elif (len(args) > 0 and args[0]) or 'img' in kwargs:
            img = args[0] if len(args) > 0 and args[0] else kwargs['img']
        else:
            raise InvalidArguments
        self._rel_vector = rel_pos_vector
        x = rel_pos_vector.x * window_width / 16
        y = rel_pos_vector.y * window_height / 9
        super(Asset, self).__init__(img=img, x=x, y=y, *args, **kwargs)
        if desired_width:
            self.scale_x = desired_width * window_width / self.image.width / 16
        if desired_height:
            self.scale_y = desired_height * window_height / self.image.height / 9

    @property
    def rel_vector(self):
        return self._rel_vector

    @property
    def rel_x(self):
        return self._rel_vector.x

    @property
    def rel_y(self):
        return self._rel_vector.y

    def set_rel_vector(self, rel_vector: Vector, window_width: int, window_height: int):
        self._rel_vector = rel_vector
        self.x = int(rel_vector.x * window_width / 16)
        self.y = int(rel_vector.y * window_height / 9)

    def set_rel_x(self, rel_x: float, window_width: int):
        self._rel_vector.x = rel_x
        self.x = int(rel_x * window_width / 16)

    def set_rel_y(self, rel_y: float, window_height: int):
        self._rel_vector.y = rel_y
        self.y = int(rel_y * window_height / 9)


class Collidable(Asset):
    """
    Anything that can collide with other objects on screen.
    """

    cell_width = 16 / 6
    cell_height = 9 / 6

    def __init__(self, points: Tuple[Tuple[float]] = None, radius: float = None, *args, **kwargs):
        """
        :param points: A tuple of tuples of floats (x,y) that describes the boundary using relative coordinates from the
         top left most point going clockwise around the perimeter. Object becomes a polygon or point.
        :param radius: A relative coordinate describing the radius of a circular boundary from the center of the object.
        Object becomes a circle.
        """
        super(Collidable, self).__init__(*args, **kwargs)
        if radius and not points:
            self.collider = Circle(self.rel_vector, radius)
        elif points and len(points) != 1:
            self.collider = Poly(self.rel_vector, points)
        elif points:
            self.collider = None
        else:
            if (len(args) > 1 and args[1]) or 'window_width' in kwargs:
                width = args[1] if len(args) > 1 and args[1] else kwargs['window_width']
            else:
                raise InvalidArguments
            if (len(args) > 2 and args[2]) or 'window_height' in kwargs:
                height = args[2] if len(args) > 2 and args[2] else kwargs['window_height']
            else:
                raise InvalidArguments
            self.collider = Poly(self.rel_vector,
                                 (
                                     Vector(self.image.width / width * 16 + self.rel_x,
                                            self.image.height / height * 9 + self.rel_y),
                                     Vector(self.image.width / width * 16 + self.rel_x,
                                            -self.image.height / height * 9 + self.rel_y),
                                     Vector(-self.image.width / width * 16 + self.rel_x,
                                            -self.image.height / height * 9 + self.rel_y),
                                     Vector(-self.image.width / width * 16 + self.rel_x,
                                            self.image.height / height * 9 + self.rel_y)))

    @property
    def cells(self) -> [int, int]:
        """
        Gives the row and column of the cell(s) that this object is in. Used for collision detection.
        """
        if not self.collider:
            result = [[floor(self.rel_x / Collidable.cell_width), floor(self.rel_y / Collidable.cell_height)]]
        elif isinstance(self.collider, Poly):
            result = []
            for point in self.collider.points:
                temp = [floor(point[0] / Collidable.cell_width), floor(point[1] / Collidable.cell_height)]
                if temp not in result:
                    result.append(temp)
        elif isinstance(self.collider, Circle):
            points = [self.rel_vector + Vector(0, self.collider.radius),
                      self.rel_vector + Vector(self.collider.radius, 0),
                      self.rel_vector + Vector(0, -self.collider.radius),
                      self.rel_vector + Vector(-self.collider.radius, 0)]
            result = []
            for point in points:
                temp = [floor(point[0] / Collidable.cell_width), floor(point[1] / Collidable.cell_height)]
                if temp not in result:
                    result.append(temp)
        else:
            return None
        return result

    def is_colliding(self, other):
        """
        Returns a collision response if the two objects are colliding, else returns None.
        """
        if isinstance(other, Collidable):
            resp = Response()
            if self.collider:
                if other.collider:
                    result = collide(self.collider, other.collider, resp)
                else:
                    result = collide(self.collider, other.rel_vector, resp)
            else:
                if other.collider:
                    result = collide(self.rel_vector, other.collider, resp)
                else:
                    result = collide(self.rel_vector, other.rel_vector, resp)
        else:
            return NotImplemented
        return resp if result else None


class PhysicsBody(Collidable):
    """
    Any object that experiences full game physics, not just collisions.
    """

    def __init__(self, dx: Vector = Vector(0, 0), d2x: Vector = Vector(0, 0), mass: float = 1, *args, **kwargs):
        """
        :param dx: velocity of the object at state 1, given with relative coordinates.
        :param d2x: acceleration of the object at state 1, given with relative coordinates.
        :param mass: mass given in mass relative to player (player mass = 1)
        """
        super(PhysicsBody, self).__init__(*args, **kwargs)
        self.dx: Vector = dx
        self.d2x: Vector = d2x
        self.mass: float = mass

    def on_update(self, dt: float, window_width: int, window_height: int):
        self.dx += self.d2x * dt
        self.set_rel_x(self.rel_x + self.dx[0] * dt, window_width)
        self.set_rel_y(self.rel_y + self.dx[1] * dt, window_height)
        for loc in self.collider.points:
            loc += self.dx

    def impulse(self, force: Vector, dt: float):
        self.dx += force * dt / self.mass


class Player(PhysicsBody):
    """
    A physics body that can be moved by a user.
    """

    def __init__(self, health: int = 100, speed: float = 2,
                 key_map: KeyMap = KeyMap(**KeyMap.defaults), *args, **kwargs):
        """
        :param health: health, an integer, defaults to 100.
        """
        super(Player, self).__init__(*args, **kwargs)
        self.key_handler = KeyStateHandler()
        self.key_binds = key_map
        self._health = health
        self.speed = speed  # measured in relative coords/sec
        self.dead = False

    @property
    def health(self):
        """
        The strength of life force keeping the user bound to their player.
        """
        return self._health

    @health.setter
    def health(self, health):
        if health < 0:
            health = 0
            self.dead = True
        self._health = health

    def on_update(self, dt: float, window_width: int, window_height: int):
        handler = self.key_handler
        binds = self.key_binds
        vec = Vector(0, 0)
        if handler[binds.up]:
            vec += Vector(0, 1)
        if handler[binds.down]:
            vec += Vector(0, -1)
        if handler[binds.right]:
            vec += Vector(1, 0)
        if handler[binds.left]:
            vec += Vector(-1, 0)
        self.dx = vec * self.speed
        super(Player, self).on_update(dt, window_width, window_height)


class InvalidArguments(Exception):
    pass
