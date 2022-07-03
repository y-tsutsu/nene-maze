import sys

from direct.gui.OnscreenText import OnscreenText
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpFunc
from direct.interval.MetaInterval import Parallel, Sequence
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (AmbientLight, BitMask32, CollisionBox,
                          CollisionHandlerQueue, CollisionNode, CollisionRay,
                          CollisionTraverser, DirectionalLight, LRotationf,
                          LVector3, Material, Point3, TextNode)


class NeneMaze(ShowBase):
    ACCEL = 70
    MAX_SPEED = 5
    MAX_SPEED_SQ = MAX_SPEED ** 2

    def __init__(self):
        super().__init__(self)

        self.disableMouse()
        camera.setPosHpr(11, -11, 25, 45, -60, 0)  # noqa: F821
        self.accept('escape', sys.exit)

        self._view_text()
        self._init_maze()
        self._init_ball()
        self._init_goal()
        self._init_light()

        self._start()

    def _view_text(self):
        font = loader.loadFont('/c/Windows/Fonts/YuGothM.ttc')  # noqa: F821
        self.title = OnscreenText(text='ねねっちの迷路',
                                  parent=base.a2dBottomRight, align=TextNode.ARight,  # noqa: F821
                                  fg=(1, 1, 1, 1), pos=(-0.1, 0.1), scale=.08, font=font, shadow=(0, 0, 0, 0.5))
        self.instructions = OnscreenText(text='えーー！なるっちの担当箇所がバグだらけ！？',
                                         parent=base.a2dTopLeft, align=TextNode.ALeft,  # noqa: F821
                                         fg=(1, 1, 1, 1), pos=(0.1, -0.15), scale=.06, font=font, shadow=(0, 0, 0, 0.5))

    def _init_maze(self):
        self._maze = loader.loadModel('models/maze')  # noqa: F821
        self._maze.reparentTo(render)  # noqa: F821

        self._walls = self._maze.find('**/wall_collide')
        self._walls.node().setIntoCollideMask(BitMask32.bit(0))

        self._ground = self._maze.find('**/ground_collide')
        self._ground.node().setIntoCollideMask(BitMask32.bit(1))

        self._lose_triggers = []
        for i in range(6):
            trigger = self._maze.find('**/hole_collide' + str(i))
            trigger.node().setIntoCollideMask(BitMask32.bit(0))
            trigger.node().setName('lose_trigger')
            self._lose_triggers.append(trigger)

    def _init_ball(self):
        self._ball_root = render.attachNewNode('ballRoot')  # noqa: F821
        self._ball = loader.loadModel('models/ball')  # noqa: F821
        self._ball.reparentTo(self._ball_root)

        self._ball_sphere = self._ball.find('**/ball')
        self._ball_sphere.node().setFromCollideMask(BitMask32.bit(0))
        self._ball_sphere.node().setIntoCollideMask(BitMask32.allOff())

        self._ball_groundRay = CollisionRay()
        self._ball_groundRay.setOrigin(0, 0, 10)
        self._ball_groundRay.setDirection(0, 0, -1)

        self._ball_ground_col = CollisionNode('groundRay')
        self._ball_ground_col.addSolid(self._ball_groundRay)
        self._ball_ground_col.setFromCollideMask(BitMask32.bit(1))
        self._ball_ground_col.setIntoCollideMask(BitMask32.allOff())
        self._ball_ground_col_np = self._ball_root.attachNewNode(self._ball_ground_col)

        self._ctrav = CollisionTraverser()
        self._chandler = CollisionHandlerQueue()
        self._ctrav.addCollider(self._ball_sphere, self._chandler)
        self._ctrav.addCollider(self._ball_ground_col_np, self._chandler)
        self.pushCTrav(self._ctrav)

    def _init_goal(self):
        self._goal = self.loader.loadModel('models/misc/rgbCube')
        self._goal.reparentTo(self.render)
        self._goal.setScale(0.1, 0.1, 0.1)
        self._goal.setPos(4, 4, -0.5)

        self._goal_col = CollisionNode('goalCol')
        self._goal_col.addSolid(CollisionBox(Point3(0, 0, 0), 3, 3, 3))
        self._goal_col.setIntoCollideMask(BitMask32.bit(0))
        _ = self._goal.attachNewNode(self._goal_col)

    def _init_light(self):
        ambient_light = AmbientLight('ambientLight')
        ambient_light.setColor((0.55, 0.55, 0.55, 1))
        directional_light = DirectionalLight('directionalLight')
        directional_light.setDirection(LVector3(0, 0, -1))
        directional_light.setColor((0.375, 0.375, 0.375, 1))
        directional_light.setSpecularColor((1, 1, 1, 1))
        self._ball_root.setLight(render.attachNewNode(ambient_light))  # noqa: F821
        self._ball_root.setLight(render.attachNewNode(directional_light))  # noqa: F821

        material = Material()
        material.setSpecular((1, 1, 1, 1))
        material.setShininess(96)
        self._ball.setMaterial(material, 1)

    def _start(self):
        start_pos = self._maze.find('**/start').getPos()
        self._ball_root.setPos(start_pos)
        self._ball_v = LVector3(0, 0, 0)
        self._accel_v = LVector3(0, 0, 0)

        taskMgr.remove('rollTask')  # noqa: F821
        self.mainLoop = taskMgr.add(self._roll_task, 'rollTask')  # noqa: F821

    def _roll_task(self, task):
        dt = globalClock.getDt()  # noqa: F821
        if dt > 0.2:
            return task.cont

        for i in range(self._chandler.getNumEntries()):
            entry = self._chandler.getEntry(i)
            name = entry.getIntoNode().getName()
            if name == 'wall_collide':
                self._wall_collide_handler(entry)
            elif name == 'ground_collide':
                self._ground_collide_handler(entry)
            elif name == 'lose_trigger':
                self._lose_game(entry)
            elif name == 'goalCol':
                self._win_game(entry)

        self._ball_v += self._accel_v * dt * NeneMaze.ACCEL
        if self._ball_v.lengthSquared() > NeneMaze.MAX_SPEED_SQ:
            self._ball_v.normalize()
            self._ball_v *= NeneMaze.MAX_SPEED
        self._ball_root.setPos(self._ball_root.getPos() + (self._ball_v * dt))
        prevRot = LRotationf(self._ball.getQuat())
        axis = LVector3.up().cross(self._ball_v)
        newRot = LRotationf(axis, 45.5 * dt * self._ball_v.length())
        self._ball.setQuat(prevRot * newRot)

        if base.mouseWatcherNode.hasMouse():  # noqa: F821
            mpos = base.mouseWatcherNode.getMouse()  # noqa: F821
            self._maze.setP(mpos.getY() * -10)
            self._maze.setR(mpos.getX() * 10)
        return task.cont

    def _wall_collide_handler(self, col_entry):
        norm = col_entry.getSurfaceNormal(render) * -1  # noqa: F821
        cur_speed = self._ball_v.length()
        in_vec = self._ball_v / cur_speed
        vel_angle = norm.dot(in_vec)
        hit_dir = col_entry.getSurfacePoint(render) - self._ball_root.getPos()  # noqa: F821
        hit_dir.normalize()
        hit_angle = norm.dot(hit_dir)

        if vel_angle > 0 and hit_angle > 0.995:
            reflect_vec = (norm * norm.dot(in_vec * -1) * 2) + in_vec
            self._ball_v = reflect_vec * (cur_speed * (((1 - vel_angle) * 0.5) + 0.5))
            disp = (col_entry.getSurfacePoint(render) - col_entry.getInteriorPoint(render))  # noqa: F821
            new_pos = self._ball_root.getPos() + disp
            self._ball_root.setPos(new_pos)

    def _ground_collide_handler(self, col_entry):
        new_z = col_entry.getSurfacePoint(render).getZ()  # noqa: F821
        self._ball_root.setZ(new_z + 0.4)
        norm = col_entry.getSurfaceNormal(render)  # noqa: F821
        accelSide = norm.cross(LVector3.up())
        self._accel_v = norm.cross(accelSide)

    def _lose_game(self, entry):
        to_pos = entry.getInteriorPoint(render)  # noqa: F821
        taskMgr.remove('rollTask')  # noqa: F821
        Sequence(Parallel(LerpFunc(self._ball_root.setX, fromData=self._ball_root.getX(), toData=to_pos.getX(), duration=0.1),
                          LerpFunc(self._ball_root.setY, fromData=self._ball_root.getY(), toData=to_pos.getY(), duration=0.1),
                          LerpFunc(self._ball_root.setZ, fromData=self._ball_root.getZ(), toData=self._ball_root.getZ() - 0.9, duration=0.2)),
                 Wait(1), Func(self._start)).start()

    def _win_game(self, entry):
        self.title.setText('ゴール！！')
        _ = entry.getInteriorPoint(render)  # noqa: F821
        self._ball_root.hide()
        taskMgr.remove('rollTask')  # noqa: F821


def main():
    game = NeneMaze()
    game.run()


if __name__ == '__main__':
    main()
