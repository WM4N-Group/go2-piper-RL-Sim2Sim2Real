"""Render the GO2-PIPER low-board push scene."""

import argparse
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image
import yaml

from reconfigurable_navigation.piper_box_runtime import add_piper_collision_excludes
from reconfigurable_navigation.piper_locomotion_runtime import DEPLOY, JOINT_NAMES, ROOT
from reconfigurable_navigation.piper_robot_profile import apply_piper_collision_profile, apply_piper_robot_profile


BOARD_POSITION = (0.94, 0.0)
BOARD_SIZE = (1.10, 0.48, 0.08)
BOARD_MASS = 2.5
BOARD_FRICTION = 0.7
PUSH_DISTANCE = 0.90
NOMINAL_BASE_HEIGHT = 0.35


def make_model():
    spec = mujoco.MjSpec.from_file(str(ROOT / "robots/go2_piper/go2piper.xml"))
    for mesh in spec.meshes:
        mesh.file = str(ROOT / "robots/go2_piper/assets" / Path(mesh.file).name)
    apply_piper_robot_profile(spec)
    apply_piper_collision_profile(spec)
    robot_bodies = [body.name for body in spec.bodies if body.name and body.name != "world"]
    add_piper_collision_excludes(spec, robot_bodies, native_collisions=True)
    spec.worldbody.add_light(pos=[1.5, -3.0, 5.0], dir=[0, 0, -1])
    spec.worldbody.add_geom(
        name="floor", type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=[0, 0, -0.1], size=[4.0, 3.0, 0.1],
        friction=[0.8, 0.02, 0.01], condim=3, priority=1, rgba=[0.30, 0.35, 0.37, 1],
    )
    body = spec.worldbody.add_body(name="low_board", pos=[*BOARD_POSITION, BOARD_SIZE[2] / 2])
    body.add_freejoint(name="low_board_joint")
    body.add_geom(
        name="low_board_geom", type=mujoco.mjtGeom.mjGEOM_BOX,
        size=np.asarray(BOARD_SIZE) / 2, mass=BOARD_MASS, friction=[BOARD_FRICTION, 0.02, 0.01],
        condim=3, priority=2, rgba=[0.67, 0.38, 0.17, 1],
    )
    return spec.compile()


def initialize_nominal_pose(model, data):
    with (DEPLOY / "config.yaml").open() as stream:
        config = yaml.safe_load(stream)
    data.qpos[:3] = [0.0, 0.0, NOMINAL_BASE_HEIGHT]
    data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]
    for name, angle in zip(JOINT_NAMES, config["default_angles"], strict=True):
        joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if joint_id < 0:
            raise ValueError(f"Missing PIPER joint: {name}")
        data.qpos[model.jnt_qposadr[joint_id]] = angle
    mujoco.mj_forward(model, data)


def check_scene(model, data):
    board_body = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "low_board")
    board_geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "low_board_geom")
    np.testing.assert_allclose(model.geom_size[board_geom] * 2, BOARD_SIZE, atol=1.0e-9)
    np.testing.assert_allclose(model.body_mass[board_body], BOARD_MASS, atol=1.0e-9)
    np.testing.assert_allclose(model.geom_friction[board_geom, 0], BOARD_FRICTION, atol=1.0e-9)
    np.testing.assert_allclose(data.xpos[board_body], (*BOARD_POSITION, BOARD_SIZE[2] / 2), atol=1.0e-9)
    for index in range(data.ncon):
        contact = data.contact[index]
        names = {
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom1),
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, contact.geom2),
        }
        if names != {"floor", "low_board_geom"} or contact.dist < -1.0e-6:
            raise AssertionError(f"Unexpected initial contact: {sorted(names)} at {contact.dist:.6f} m")
    return {
        "board_position": (*BOARD_POSITION, BOARD_SIZE[2] / 2),
        "board_size": BOARD_SIZE,
        "board_mass": BOARD_MASS,
        "board_friction": BOARD_FRICTION,
        "push_target": (BOARD_POSITION[0] + PUSH_DISTANCE, BOARD_POSITION[1]),
        "initial_contacts": data.ncon,
    }


def render_scene(output):
    model = make_model()
    model.vis.global_.offwidth = 1280
    model.vis.global_.offheight = 720
    data = mujoco.MjData(model)
    initialize_nominal_pose(model, data)
    report = check_scene(model, data)

    camera = mujoco.MjvCamera()
    camera.lookat[:] = [0.65, 0.0, 0.15]
    camera.distance = 3.8
    camera.azimuth = 120
    camera.elevation = -28
    with mujoco.Renderer(model, height=720, width=1280) as renderer:
        renderer.update_scene(data, camera)
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(renderer.render()).save(output)
    return output, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(render_scene(parser.parse_args().output))