# Copyright (c) 2022 NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import unittest

import warp as wp
import warp.sim
import math
from warp.tests.test_base import *

wp.init()


def build_ant(num_envs):
    builder = wp.sim.ModelBuilder()
    for i in range(num_envs):
        wp.sim.parse_mjcf(
            os.path.join(os.path.dirname(__file__), "../../examples/assets/nv_ant.xml"),
            builder,
            up_axis="y",
        )

        coord_count = 15
        dof_count = 14

        coord_start = i * coord_count
        dof_start = i * dof_count

        # base
        builder.joint_q[coord_start : coord_start + 3] = [i * 2.0, 0.70, 0.0]
        builder.joint_q[coord_start + 3 : coord_start + 7] = wp.quat_from_axis_angle((1.0, 0.0, 0.0), -math.pi * 0.5)

        # joints
        builder.joint_q[coord_start + 7 : coord_start + coord_count] = [0.0, 1.0, 0.0, -1.0, 0.0, -1.0, 0.0, 1.0]
        builder.joint_qd[dof_start + 6 : dof_start + dof_count] = [1.0, 1.0, 1.0, -1.0, 1.0, -1.0, 1.0, 1.0]

    return builder


def build_complex_joint_mechanism(chain_length):
    builder = wp.sim.ModelBuilder()
    com0 = wp.vec3(1.0, 2.0, 3.0)
    com1 = wp.vec3(4.0, 5.0, 6.0)
    com2 = wp.vec3(7.0, 8.0, 9.0)
    ax0 = wp.normalize(wp.vec3(-1.0, 2.0, 3.0))
    ax1 = wp.normalize(wp.vec3(4.0, -1.0, 2.0))
    ax2 = wp.normalize(wp.vec3(-3.0, 4.0, -1.0))
    # declare some transforms with nonzero translation and orientation
    tf0 = wp.transform(wp.vec3(1.0, 2.0, 3.0), wp.quat_from_axis_angle((1.0, 0.0, 0.0), math.pi * 0.25))
    tf1 = wp.transform(wp.vec3(4.0, 5.0, 6.0), wp.quat_from_axis_angle((0.0, 1.0, 0.0), math.pi * 0.5))
    tf2 = wp.transform(wp.vec3(7.0, 8.0, 9.0), wp.quat_from_axis_angle((0.0, 0.0, 1.0), math.pi * 0.75))

    parent = -1
    for i in range(chain_length):
        b0 = builder.add_body(com=com0)
        builder.add_joint_fixed(parent=parent, child=b0, parent_xform=tf1, child_xform=tf0)
        assert builder.articulation_count == 1

        b1 = builder.add_body(com=com1)
        builder.add_joint_revolute(parent=b0, child=b1, parent_xform=tf1, child_xform=tf2, axis=ax1)
        builder.joint_q[-1] = 0.3
        builder.joint_qd[-1] = 1.0

        b2 = builder.add_body(com=com2)
        builder.add_joint_universal(parent=b1, child=b2, parent_xform=tf2, child_xform=tf0, axis_0=ax0, axis_1=ax1)
        builder.joint_q[-2:] = [0.3, 0.5]
        builder.joint_qd[-2:] = [1.0, -1.0]

        b3 = builder.add_body(com=com0)
        builder.add_joint_ball(parent=b2, child=b3, parent_xform=tf0, child_xform=tf1)
        builder.joint_q[-4:] = list(wp.quat_from_axis_angle(ax0, 0.7))
        builder.joint_qd[-3:] = [1.0, -0.6, 1.5]

        b4 = builder.add_body(com=com1)
        builder.add_joint_compound(
            parent=b3,
            child=b4,
            parent_xform=tf2,
            child_xform=tf1,
            axis_0=(0, 0, 1),
            axis_1=(1, 0, 0),
            axis_2=(0, 1, 0),
        )
        builder.joint_q[-3:] = [0.3, 0.5, 0.27]
        builder.joint_qd[-3:] = [1.23, -1.0, 0.5]

        b5 = builder.add_body(com=com2)
        builder.add_joint_prismatic(
            parent=b4,
            child=b5,
            parent_xform=tf2,
            child_xform=tf0,
            axis=ax0,
        )
        builder.joint_q[-1] = 0.92
        builder.joint_qd[-1] = -0.63

        b6 = builder.add_body(com=com0)
        builder.add_joint_d6(
            parent=b5,
            child=b6,
            parent_xform=tf0,
            child_xform=tf2,
            linear_axes=[ax0, ax1, wp.cross(ax0, ax1)],
            angular_axes=[ax1, ax2, wp.cross(ax1, ax2)],
        )
        builder.joint_q[-6:] = [0.3, 0.5, 0.7, 0.9, 1.1, 1.3]
        builder.joint_qd[-6:] = [1.0, -1.0, 0.5, 0.8, -0.3, 0.1]

        b7 = builder.add_body(com=com1)
        builder.add_joint_free(
            parent=b6,
            child=b7,
            parent_xform=tf1,
            child_xform=tf2,
        )
        builder.joint_q[-7:] = [0.5, -0.9, 1.4] + list(wp.quat_rpy(0.3, -0.5, 0.7))
        builder.joint_qd[-6:] = [1.0, -1.0, 0.5, 0.8, -0.3, 0.1]

        b8 = builder.add_body(com=com2)
        builder.add_joint_distance(
            parent=b7,
            child=b8,
            parent_xform=tf1,
            child_xform=tf2,
        )
        builder.joint_q[-7:] = [-0.3, -0.7, 0.2] + list(wp.quat_rpy(0.1, 0.1, 0.4))
        builder.joint_qd[-6:] = [-0.34, 0.5, -0.6, -0.4, 0.2, 0.1]

        # D6 joint that behaves like a fixed joint
        b9 = builder.add_body(com=com0)
        builder.add_joint_d6(
            parent=b8,
            child=b9,
            parent_xform=tf0,
            child_xform=tf2,
            linear_axes=[],
            angular_axes=[],
        )

        b10 = builder.add_body(com=com0)
        builder.add_joint_d6(
            parent=b9,
            child=b10,
            parent_xform=tf1,
            child_xform=tf2,
            linear_axes=[ax1],
            angular_axes=[ax2, ax0],
        )
        builder.joint_q[-3:] = [0.3, 0.5, 0.7]
        builder.joint_qd[-3:] = [1.0, -1.0, 0.5]

        b11 = builder.add_body(com=com1)
        builder.add_joint_d6(
            parent=b10,
            child=b11,
            parent_xform=tf1,
            child_xform=tf2,
            linear_axes=[ax1, ax0, wp.cross(ax1, ax0)],
            angular_axes=[],
        )
        builder.joint_q[-3:] = [0.3, 0.5, 0.7]
        builder.joint_qd[-3:] = [1.0, -1.0, 0.5]

        b12 = builder.add_body(com=com2)
        builder.add_joint_d6(
            parent=b11,
            child=b12,
            parent_xform=tf1,
            child_xform=tf2,
            linear_axes=[],
            angular_axes=[ax1, ax2, wp.cross(ax1, ax2)],
        )
        builder.joint_q[-3:] = [0.3, 0.5, 0.7]
        builder.joint_qd[-3:] = [1.0, -1.0, 0.5]

        parent = b12

    return builder


def check_fk_ik(builder, device):
    model = builder.finalize(device)
    state = model.state()

    q_fk = model.joint_q.numpy()
    qd_fk = model.joint_qd.numpy()

    wp.sim.eval_fk(model, model.joint_q, model.joint_qd, None, state)

    q_ik = wp.zeros_like(model.joint_q)
    qd_ik = wp.zeros_like(model.joint_qd)

    wp.sim.eval_ik(model, state, q_ik, qd_ik)

    # adjust numpy print settings
    # np.set_printoptions(precision=4, floatmode="fixed", suppress=True)
    # print("q:")
    # print(np.array(q_fk))
    # print(q_ik.numpy())

    # print("qd:")
    # print(np.array(qd_fk))
    # print(qd_ik.numpy())

    assert_np_equal(q_ik.numpy(), q_fk, tol=1e-4)
    assert_np_equal(qd_ik.numpy(), qd_fk, tol=1e-4)


def test_fk_ik_ant(test, device):
    builder = build_ant(3)
    check_fk_ik(builder, device)


def test_fk_ik_complex_joint_mechanism(test, device):
    builder = build_complex_joint_mechanism(2)
    check_fk_ik(builder, device)


def register(parent):
    devices = get_test_devices()

    class TestGrad(parent):
        pass

    add_function_test(TestGrad, "test_fk_ik_ant", test_fk_ik_ant, devices=devices)
    add_function_test(
        TestGrad, "test_fk_ik_complex_joint_mechanism", test_fk_ik_complex_joint_mechanism, devices=devices
    )

    return TestGrad


if __name__ == "__main__":
    wp.build.clear_kernel_cache()
    _ = register(unittest.TestCase)
    unittest.main(verbosity=2, failfast=False)
