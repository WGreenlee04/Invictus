from client.logic import Asset

import pyglet
from pathlib import Path
import os


def start():
    """
    The main function of the client.
    """
    window = pyglet.window.Window()
    asset_batch = pyglet.graphics.Batch()
    overlay_batch = pyglet.graphics.Batch()

    objects: [Asset] = []

    resource_path = Path('resources/')
    audio_path = resource_path.joinpath('audio/')
    image_path = resource_path.joinpath('images/')
    level_path = resource_path.joinpath('levels/')

    @window.event
    def on_draw():
        window.clear()
        asset_batch.draw()
        overlay_batch.draw()

    if not os.path.exists(resource_path) or not os.path.exists(audio_path) or not os.path.exists(image_path):
        txt = pyglet.text.Label('Missing resource files, please reinstall.', font_name='Times New Roman',
                                font_size=20, x=window.width//2, y=window.height//2,
                                anchor_x='center', anchor_y='center', batch=overlay_batch)
        objects.append(txt)
        pyglet.app.run()
        return

    if not os.path.exists(level_path):
        os.mkdir(level_path)

    pyglet.app.run()


if __name__ == '__main__':
    start()
