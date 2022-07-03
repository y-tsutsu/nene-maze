import sys

from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from panda3d.core import BitMask32, TextNode


class NeneMaze(ShowBase):
    def __init__(self):
        super().__init__(self)

        self.disableMouse()
        camera.setPosHpr(11, -11, 25, 45, -60, 0)  # noqa: F821
        self.accept('escape', sys.exit)

        self._view_text()
        self._create_maze()

    def _view_text(self):
        font = loader.loadFont('/c/Windows/Fonts/YuGothM.ttc')  # noqa: F821
        self.title = OnscreenText(text='ねねっちの迷路',
                                  parent=base.a2dBottomRight, align=TextNode.ARight,  # noqa: F821
                                  fg=(1, 1, 1, 1), pos=(-0.1, 0.1), scale=.08, font=font, shadow=(0, 0, 0, 0.5))
        self.instructions = OnscreenText(text='マウスを動かすと迷路を傾けることができます',
                                         parent=base.a2dTopLeft, align=TextNode.ALeft,  # noqa: F821
                                         fg=(1, 1, 1, 1), pos=(0.1, -0.15), scale=.06, font=font, shadow=(0, 0, 0, 0.5))

    def _create_maze(self):
        self._maze = loader.loadModel('models/maze')   # noqa: F821
        self._maze.reparentTo(render)  # noqa: F821

        self._walls = self._maze.find('**/wall_collide')
        self._walls.node().setIntoCollideMask(BitMask32.bit(0))

        self._ground = self._maze.find('**/ground_collide')
        self._ground.node().setIntoCollideMask(BitMask32.bit(1))

        self._lose_triggers = []
        for i in range(6):
            trigger = self._maze.find('**/hole_collide' + str(i))
            trigger.node().setIntoCollideMask(BitMask32.bit(0))
            trigger.node().setName('loseTrigger')
            self._lose_triggers.append(trigger)


def main():
    game = NeneMaze()
    game.run()


if __name__ == '__main__':
    main()
