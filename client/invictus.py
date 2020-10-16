import configparser
import os
from pathlib import Path

import pyglet
from collision import Vector

from client.logic import Asset, Collidable, PhysicsBody, Player


def start():
    """
    The main function of the client.
    """
    temp_window = pyglet.window.Window(caption='InvictusClient', visible=False)
    asset_batch = pyglet.graphics.Batch()
    overlay_batch = pyglet.graphics.Batch()

    objects: [Asset] = []
    collidables: [Collidable] = []
    physics_objects: [PhysicsBody] = []
    players: [Player] = []

    resource_path = Path('resources/')
    audio_path = resource_path.joinpath('audio/')
    image_path = resource_path.joinpath('images/')
    level_path = resource_path.joinpath('levels/')
    config_file = resource_path.joinpath('config.ini')

    if not os.path.exists(resource_path) or not os.path.exists(audio_path) or not os.path.exists(image_path):
        txt = pyglet.text.Label('Missing resource files, please reinstall.', font_name='Times New Roman',
                                font_size=20, x=temp_window.width // 2, y=temp_window.height // 2,
                                anchor_x='center', anchor_y='center', batch=overlay_batch)
        objects.append(txt)
        temp_window.set_visible()
        pyglet.app.run()
        return
    else:
        temp_window.close()

    if not os.path.exists(level_path):
        os.mkdir(level_path)

    if not os.path.exists(config_file):
        config = configparser.ConfigParser()
        config['Client'] = {
            'resolution': '1920x1080',
            'fullscreen': 'False',
            'windowstyle': 'Borderless',
            'monitor': '0',
            'vsync': 'False'
        }
        with open(config_file, 'w') as f:
            config.write(f)
    else:
        config = configparser.ConfigParser()
        config.read(config_file)

    style = None if config['Client']['windowstyle'].lower() == 'default' else config['Client']['windowstyle'].lower()
    resolution = config['Client']['resolution'].split('x')
    window = pyglet.window.Window(caption='InvictusClient', width=int(resolution[0]), height=int(resolution[1]),
                                  style=style, fullscreen=config['Client']['fullscreen'].lower() == 'true',
                                  screen=pyglet.canvas.get_display().get_screens()[int(config['Client']['monitor'])],
                                  vsync=config['Client']['vsync'].lower() == 'true')
    del style, resolution

    pyglet.resource.path = [str(resource_path), str(image_path), str(audio_path), str(level_path)]
    test_obj = Collidable(rel_pos_vector=Vector(0, 0), window_width=window.width, window_height=window.height,
                          image_path='green.png', batch=asset_batch)
    collidables.append(test_obj)
    test_plyr = Player(rel_pos_vector=Vector(16, 9), window_width=window.width, window_height=window.height,
                       image_path='blue.png', batch=asset_batch)
    window.push_handlers(test_plyr.key_handler)
    collidables.append(test_obj)
    collidables.append(test_plyr)
    physics_objects.append(test_plyr)
    players.append(test_plyr)

    @window.event
    def on_draw():
        window.clear()
        asset_batch.draw()
        overlay_batch.draw()

    def update(dt, window_width, window_height):
        cells: {Collidable} = {}
        for collidable in collidables:
            for cell in collidable.cells:
                if (cell[0] * cell[1]) not in cells:
                    cells[cell[0] * cell[1]] = []
                cells[cell[0] * cell[1]].append(collidable)
        for cell in cells:
            for collidable in cells[cell]:
                for collidable2 in cells[cell]:
                    if collidable.is_colliding(collidable2):
                        print("Colliding")
        for player in players:
            player.on_update(dt, window_width, window_height)

    pyglet.clock.schedule_interval(update, 1 / 120, window_width=window.width, window_height=window.height)
    pyglet.app.run()


if __name__ == '__main__':
    start()
