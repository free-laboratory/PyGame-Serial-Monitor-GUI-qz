# listener.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray


class SliderEventListener(Node):
    def __init__(self, topic="/gui/slider_moved"):
        super().__init__("slider_event_listener")
        self._sub = self.create_subscription(
            Int32MultiArray, topic, self._cb, 10
        )
        self.get_logger().info(f"Listening on {topic}")

    def _cb(self, msg: Int32MultiArray):
        if len(msg.data) < 2:
            self.get_logger().warn(f"Bad message: {msg.data}")
            return
        idx, val = msg.data[0], msg.data[1]
        # idx is 0-based in the GUI
        self.get_logger().info(f"Slider S{idx+1} moved to {val}")


def main():
    rclpy.init()
    node = SliderEventListener()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()