#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray

TOPIC = "/gui/slider_moved"

class SliderEventPublisher(Node):
    def __init__(self):
        super().__init__("slider_event_publisher")
        self.publisher = self.create_publisher(Int32MultiArray, TOPIC, 10)
        self.value = 0
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.get_logger().info(f"Publishing on {TOPIC}")

    def timer_callback(self):
        msg = Int32MultiArray()
        msg.data = [0, self.value]
        self.publisher.publish(msg)
        self.get_logger().info(f"Published: {msg.data}")
        self.value = (self.value + 1) % 101

def main():
    rclpy.init()
    node = SliderEventPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()