import pygame

from pygame_gui.elements import UIButton
from pygame_gui.elements import UITextEntryLine
from pygame_gui.elements import UIDropDownMenu
from pygame_gui.elements import UILabel
from pygame_gui.elements.ui_text_box import UITextBox

#ros2 imports
import threading
import atexit
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray


def recreate_ui_helperfunction(something):
    something.ui_manager.set_window_resolution(something.options.resolution)
    something.ui_manager.clear_and_reset()

    something.background_surface = pygame.Surface(something.options.resolution)
    something.background_surface.fill(something.ui_manager.get_theme().get_colour('dark_bg'))

    current_resolution_string = (str(something.options.resolution[0]) +
                                    'x' +
                                    str(something.options.resolution[1]))
    something.test_drop_down = UIDropDownMenu(options_list=['1024x768', '1200x800', '1440x800', '1600x900', '800x600', '600x800'],
                                            starting_option=current_resolution_string,
                                            relative_rect = pygame.Rect((int(something.options.resolution[0] * 0.01),
                                                        int(something.options.resolution[1] * 0.01)),
                                                        (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
                                            manager = something.ui_manager)

    
    something.serial_select_dropdown = UIDropDownMenu(
        options_list=['not selected'],
        starting_option='not selected',
        relative_rect = pygame.Rect((int(something.options.resolution[0] * 0.99) - int(something.options.resolution[0] / 4),
                        int(something.options.resolution[1] * 0.01)),
                        (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
        manager = something.ui_manager,
        )
    
    something.serial_refresh_button = UIButton(
        pygame.Rect((int(something.options.resolution[0] * 0.99) - int(something.options.resolution[0] / 4),
                        int(something.options.resolution[1] * 0.01)+int(something.options.resolution[1] / 32)),
                        (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
        'Refresh COM Ports',
        something.ui_manager)

    something.serial_connect_button = UIButton(
        pygame.Rect((int(something.options.resolution[0] * 0.99) - int(something.options.resolution[0] / 4),
                        int(something.options.resolution[1] * 0.01)+int(something.options.resolution[1] / 16)),
                        (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
        'Press to Connect',
        something.ui_manager)
    
    #test button
    something.serial_test_button = UIButton(
        pygame.Rect((int(something.options.resolution[0] * 0.99) - int(something.options.resolution[0] / 4),
                        int(something.options.resolution[1] * 0.01)+int(something.options.resolution[1] /8)),
                        (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
        'Test Button',
        something.ui_manager)

    something.serial_baudrate_textbox = UITextEntryLine(
        relative_rect=pygame.Rect((int(something.options.resolution[0] * 0.99) - int(something.options.resolution[0] / 4),
                        int(something.options.resolution[1] * 0.01)+int(something.options.resolution[1] / 32 * 3)),
                        (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
        manager=something.ui_manager,
        initial_text="115200"
    )
    
    something.serial_monitor_mode_header_textbox = UILabel (
        relative_rect= pygame.Rect((int(something.options.resolution[0] * 0.01),
                    int(something.options.resolution[1] * 0.01)+int(something.options.resolution[1] / 32 * 1)),
                    (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
        text="Select serial output method"
    )

    something.serial_monitor_mode = UIDropDownMenu(
        options_list=['In app', 'In terminal', 'Disable'],
        starting_option='In app',
        relative_rect= pygame.Rect((int(something.options.resolution[0] * 0.01),
                    int(something.options.resolution[1] * 0.01)+int(something.options.resolution[1] / 32 * 2)),
                    (int(something.options.resolution[0] / 4), int(something.options.resolution[1] / 32))),
        manager=something.ui_manager,
        object_id="#serialmonitor"
    )

    something.serial_msg_disp = UITextBox(
        html_text="",
        relative_rect=pygame.Rect((int(something.options.resolution[0] * 0.01 + something.options.resolution[0] / 4),
                    int(something.options.resolution[1] * 0.01 + something.options.resolution[1] / 32)),
                    (int(something.options.resolution[0] / 2 - something.options.resolution[0] * 0.02), int(something.options.resolution[1] * 28 / 32))),
        manager=something.ui_manager
    )

    something.serial_msg_entry = UITextEntryLine(
        relative_rect=pygame.Rect((int(something.options.resolution[0] * 0.01 + something.options.resolution[0] / 4),
                    int(something.options.resolution[1] * 0.01)),
                    (int(something.options.resolution[0] / 2 - something.options.resolution[0] * 0.02), int(something.options.resolution[1] / 32))), 
        manager=something.ui_manager,
        object_id='#serial_text_entry'
    )

    something.serial_msg_entry.set_text('')



#########################ros2 block################################
_ROS_TOPIC = "/gui/slider_moved"
_ros_node = None
_ros_pub = None
_ros_spin_thread = None
_ros_lock = threading.Lock()

class _GuiRosPublisher(Node):
    def __init__(self):
        super().__init__("gui_slider_publisher")
        self.pub = self.create_publisher(Int32MultiArray, _ROS_TOPIC, 10)
        self.get_logger().info(f"GUI publishing slider events on {_ROS_TOPIC}")

def _ensure_ros():
    global _ros_node, _ros_pub, _ros_spin_thread
    if _ros_node is not None:
        return

    # avoid double-init issues
    if not rclpy.ok():
        rclpy.init(args=None)

    _ros_node = _GuiRosPublisher()
    _ros_pub = _ros_node.pub

    def _spin():
        try:
            rclpy.spin(_ros_node)
        except Exception:
            pass

    _ros_spin_thread = threading.Thread(target=_spin, daemon=True)
    _ros_spin_thread.start()

def _shutdown_ros():
    global _ros_node
    try:
        if _ros_node is not None:
            _ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    except Exception:
        pass

atexit.register(_shutdown_ros)
#########################ros2 block################################



# def on_slider_changed(idx: int, value: int, send_fn=None):
#     print(f"S{idx+1} -> {int(value)}")

#     if callable(send_fn):
#         try:
#             send_fn(f"S{idx+1}={int(value)}")
#         except Exception:
#             pass

#     try:
#         _ensure_ros()
#         with _ros_lock:
#             msg = Int32MultiArray()
#             msg.data = [int(idx), int(value)]
#             _ros_pub.publish(msg)
#     except Exception as e:
#         print(f"[ROS publish skipped] {e}")

from ros_slider_bridge import set_slider_and_publish

def on_slider_changed(idx, val):
    print(f"Slider {idx+1} changed to {val}")
    set_slider_and_publish(idx, val)