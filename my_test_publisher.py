#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray

TOPIC = "/gui/slider_moved"

class Pub(Node):
    def __init__(self):
        super().__init__("slider_event_publisher")
        self.pub = self.create_publisher(Int32MultiArray, TOPIC, 10)
        self.i = 0
        self.timer = self.create_timer(1.0, self.tick)
        self.get_logger().info(f"Publishing on {TOPIC}")

    def tick(self):
        msg = Int32MultiArray()
        msg.data = [0, self.i]
        self.pub.publish(msg)
        self.get_logger().info(f"Published {msg.data}")
        self.i = (self.i + 1) % 101

def main():
    rclpy.init()
    node = Pub()
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