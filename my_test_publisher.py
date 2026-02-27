# publisher.py
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray


class SliderEventPublisher(Node):
    def __init__(self, topic="/gui/slider_moved"):
        super().__init__("slider_event_publisher")
        self._pub = self.create_publisher(Int32MultiArray, topic, 10)
        self._lock = threading.Lock()
        self.get_logger().info(f"Publishing slider events on {topic}")

    def publish_slider(self, idx: int, val: int):
        with self._lock:
            msg = Int32MultiArray()
            msg.data = [int(idx), int(val)]
            self._pub.publish(msg)
