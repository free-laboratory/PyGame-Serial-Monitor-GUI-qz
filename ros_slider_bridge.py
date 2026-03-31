import math
import threading
from typing import List

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class Arm12Bridge(Node):
    def __init__(self):
        super().__init__("arm12_gui_bridge")
        self.publisher = self.create_publisher(
            JointTrajectory,
            "/joint_trajectory_controller/joint_trajectory",
            10,
        )

        self.joint_names = [f"joint_{i}" for i in range(1, 13)]
        self.current_targets = [0.0] * 12

    @staticmethod
    def slider_to_radians(value: float) -> float:
        """
        Map slider range 1..100 to joint range -pi..pi
        """
        value = max(1.0, min(100.0, float(value)))
        ratio = (value - 1.0) / 99.0
        return -math.pi + ratio * (2.0 * math.pi)

    def update_joint_from_slider(self, slider_idx: int, slider_value: float) -> None:
        if not 0 <= slider_idx < 12:
            return
        self.current_targets[slider_idx] = self.slider_to_radians(slider_value)

    def publish_all(self, move_time_sec: float = 0.3) -> None:
        msg = JointTrajectory()
        msg.joint_names = self.joint_names

        point = JointTrajectoryPoint()
        point.positions = list(self.current_targets)
        point.time_from_start.sec = int(move_time_sec)
        point.time_from_start.nanosec = int((move_time_sec % 1.0) * 1e9)

        msg.points = [point]
        self.publisher.publish(msg)


_bridge = None
_spin_thread = None


def start_ros_bridge():
    global _bridge, _spin_thread

    if _bridge is not None:
        return _bridge

    rclpy.init(args=None)
    _bridge = Arm12Bridge()

    def spin():
        rclpy.spin(_bridge)

    _spin_thread = threading.Thread(target=spin, daemon=True)
    _spin_thread.start()
    return _bridge


def stop_ros_bridge():
    global _bridge
    if _bridge is not None:
        _bridge.destroy_node()
        rclpy.shutdown()
        _bridge = None


def set_slider_and_publish(slider_idx: int, slider_value: float):
    bridge = start_ros_bridge()
    bridge.update_joint_from_slider(slider_idx, slider_value)
    bridge.publish_all()