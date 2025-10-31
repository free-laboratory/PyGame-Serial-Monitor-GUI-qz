import pygame
import pygame_gui
from collections import deque
import random

#import pygame_widgets
#from pygame_widgets.slider import Slider
#from pygame_widgets.textbox import TextBox

import serial
import serial.tools.list_ports
import os
import re

from pygame_gui import UIManager, PackageResource

from pygame_gui.elements import UIButton
from pygame_gui.elements import UITextEntryLine
from pygame_gui.elements import UIDropDownMenu
from pygame_gui.elements import UILabel
from pygame_gui.elements.ui_text_box import UITextBox

from pygame_gui.windows import UIMessageWindow

import gvar_ctrl
import event_functions

enable_serial_monitor = 1 # 0-disable 1-in app 2-in terminal

serial_msg_text = ""
joysticks = None


class Options:
    def __init__(self):
        self.resolution = (600, 800)
        self.fullscreen = False

class OptionsUIApp:
    def __init__(self):
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (100,45)
        pygame.init()
        pygame.display.set_caption("Options UI")
        self.options = Options()

        if self.options.fullscreen:
            self.window_surface = pygame.display.set_mode(self.options.resolution,
                                                          pygame.FULLSCREEN)
        else:
            self.window_surface = pygame.display.set_mode(self.options.resolution)

        self.background_surface = None

        self.ui_manager = UIManager(self.options.resolution,
                                    PackageResource(package='data.themes',
                                                    resource='theme_2.json'))
        self.ui_manager.preload_fonts([{'name': 'fira_code', 'point_size': 10, 'style': 'bold'},
                                       {'name': 'fira_code', 'point_size': 10, 'style': 'regular'},
                                       {'name': 'fira_code', 'point_size': 10, 'style': 'italic'},
                                       {'name': 'fira_code', 'point_size': 14, 'style': 'italic'},
                                       {'name': 'fira_code', 'point_size': 14, 'style': 'bold'}
                                       ])

        
        self.test_drop_down = None

        self.serial_monitor_mode_header_textbox = None
        self.serial_monitor_mode = None

        self.serial_select_dropdown = None
        self.serial_connect_button = None
        self.serial_refresh_button = None
        self.serial_baudrate_textbox = None
        self.serial_test_button = None #test button

        self.serial_msg_disp = None
        self.serial_msg_entry = None

        self.recreate_ui()

        self.clock = pygame.time.Clock()
        self.time_delta_stack = deque([])

        self.button_response_timer = pygame.time.Clock()
        self.running = True
        self.debug_mode = False

        self.all_enabled = True
        self.all_shown = True

    def _create_sliders(self):
        """
        12 pygame_gui sliders (1–100), 6 left + 6 right.
        Compact layout; value label always wide enough for '100';
        clamps to window edges to avoid going off-screen; anchored near
        the bottom of the big center box.
        """
        # Remove old widgets if rebuilding
        if hasattr(self, "_slider_rows"):
            for row in self._slider_rows:
                row['label'].kill(); row['slider'].kill(); row['value'].kill()
        self._slider_rows = []

        W, H = self.options.resolution
        margin = 12

        # Scale a bit with window width (compact but readable)
        # clamp between 0.75x and 1.0x of "normal"
        scale = max(0.75, min(1.0, W / 1200.0))

        # Anchor to the big center box from your helper
        box = getattr(self, "serial_msg_disp", None)
        if box is not None and hasattr(box, "relative_rect"):
            box_rect = box.relative_rect
        else:
            box_rect = pygame.Rect(int(W * 0.2), 100, int(W * 0.6), int(H * 0.65))

        # Horizontal bands: LEFT = [margin .. box.left - margin]
        # RIGHT = [box.right + margin .. W - margin] (scales with window width)
        left_band_start  = margin
        left_band_end    = max(left_band_start + 120, box_rect.left - margin)

        right_band_start = box_rect.right + margin
        right_band_end   = max(right_band_start + 120, W - margin)

        # Clamp bands inside window
        left_band_end  = min(left_band_end, W - margin)
        right_band_end = min(right_band_end, W - margin)

        # Row sizing (compact)
        per_col = 6
        PAD_Y   = int(6 * scale)
        ROW_MIN = int(22 * scale)
        ROW_MAX = int(36 * scale)

        # Controls widths (compact but visible)
        LABEL_W = max(24, int(28 * scale))         # "S12" fits
        VALUE_W = max(34, int(36 * scale))         # room for "100"
        GAP_L_S = max(6,  int(6 * scale))
        GAP_S_V = max(6,  int(6 * scale))
        SLIDER_MIN_W = max(90, int(100 * scale))   # slider can get small but usable

        def side_metrics(start_px: int, end_px: int):
            """Compute slider/value geometry per side and keep inside window."""
            band_w = max(140, end_px - start_px)
            value_x = start_px + band_w - VALUE_W                 # value right-aligned to band
            slider_x = start_px + LABEL_W + GAP_L_S
            slider_w = max(SLIDER_MIN_W, value_x - GAP_S_V - slider_x)
            # If the band is too tiny, shove value next to label and keep slider min size.
            if slider_w < SLIDER_MIN_W:
                slider_w = SLIDER_MIN_W
                value_x  = slider_x + slider_w + GAP_S_V
            return slider_x, slider_w, value_x, start_px

        l_slider_x, l_slider_w, l_value_x, l_base_x = side_metrics(left_band_start, left_band_end)
        r_slider_x, r_slider_w, r_value_x, r_base_x = side_metrics(right_band_start, right_band_end)

        # Vertical layout: anchor near the bottom of the box
        bottom_margin = max(10, int(12 * scale))
        usable_h = max(180, box_rect.height - (bottom_margin + 12))
        row_h = max(ROW_MIN, min(ROW_MAX, (usable_h - (per_col - 1) * PAD_Y) // per_col))
        total_block_h = per_col * row_h + (per_col - 1) * PAD_Y
        top_y = max(box_rect.top + 12, box_rect.bottom - bottom_margin - total_block_h)

        # Optional small header
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(box_rect.centerx - 50, max(0, box_rect.top - 20), 100, 16),
            text="Controls",
            manager=self.ui_manager
        )

        slider_min, slider_max, default = 1, 100, 50
        items = []

        for i in range(12):
            col = 0 if i < 6 else 1
            row = i if i < 6 else (i - 6)
            y   = top_y + row * (row_h + PAD_Y)

            if col == 0:
                base_x   = l_base_x
                s_x, s_w = l_slider_x, l_slider_w
                v_x      = l_value_x
            else:
                base_x   = r_base_x
                s_x, s_w = r_slider_x, r_slider_w
                v_x      = r_value_x

            # Final clamp so nothing goes off-screen horizontally
            s_w = max(SLIDER_MIN_W, min(s_w, W - margin - s_x - GAP_S_V - VALUE_W))
            v_x = min(v_x, W - margin - VALUE_W)

            label_rect  = pygame.Rect(base_x, y, LABEL_W, row_h)
            slider_rect = pygame.Rect(s_x,    y + 3, s_w,  row_h - 6)
            value_rect  = pygame.Rect(v_x,    y,     VALUE_W, row_h)

            lbl = pygame_gui.elements.UILabel(label_rect, f"S{i+1}", manager=self.ui_manager)
            sld = pygame_gui.elements.UIHorizontalSlider(slider_rect, default, (slider_min, slider_max), manager=self.ui_manager)
            val = pygame_gui.elements.UILabel(value_rect, str(default), manager=self.ui_manager)

            items.append({'label': lbl, 'slider': sld, 'value': val})

        self._slider_rows = items







    def recreate_ui(self):
        event_functions.recreate_ui_helperfunction(self)
        self._create_sliders()

    def create_message_window(self):
        self.button_response_timer.tick()
        self.message_window = UIMessageWindow(
            rect=pygame.Rect((random.randint(0, self.options.resolution[0] - 300),
                              random.randint(0, self.options.resolution[1] - 200)),
                             (300, 250)),
            window_title='Test Message Window',
            html_message='this is a message',
            manager=self.ui_manager)
        time_taken = self.button_response_timer.tick() / 1000.0
        # currently taking about 0.35 seconds down from 0.55 to create
        # an elaborately themed message window.
        # still feels a little slow but it's better than it was.
        print("Time taken to create message window: " + str(time_taken))

    def check_resolution_changed(self):
        print(self.test_drop_down.selected_option)
        resolution_string = self.test_drop_down.selected_option[0].split('x')
        resolution_width = int(resolution_string[0])
        resolution_height = int(resolution_string[1])
        if (resolution_width != self.options.resolution[0] or
                resolution_height != self.options.resolution[1]):
            self.options.resolution = (resolution_width, resolution_height)
            self.window_surface = pygame.display.set_mode(self.options.resolution)
            self.recreate_ui()



    def process_events(self):
        global enable_serial_monitor
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            self.ui_manager.process_events(event)

            # --- handle built-in slider moves ---
            is_slider_event = (
                (event.type == pygame.USEREVENT and getattr(event, "user_type", None) == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED)
                or (event.type == getattr(pygame_gui, "UI_HORIZONTAL_SLIDER_MOVED", None))
            )
            if is_slider_event and hasattr(self, "_slider_rows"):
                for idx, row in enumerate(self._slider_rows):
                    if event.ui_element is row['slider']:
                        val = int(row['slider'].get_current_value())
                        row['value'].set_text(str(val))
                        break   


            if (event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED):
                if (event.ui_object_id == '#main_text_entry'):
                    print("main: " + event.text)
                if (event.ui_object_id == '#serial_text_entry'):
                    try:
                        str_to_be_sent = event.text
                        utf8str = str_to_be_sent.encode('utf-8') + b'\n'
                        print("Sent: ", end="")
                        print(utf8str)
                        gvar_ctrl.mcu_serial_object.write(utf8str)
                        self.serial_msg_entry.set_text("")
                    except:
                        print("Send failed!")
                    

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.serial_connect_button:
                    try:
                        print("--Connecting to {}".format(self.serial_select_dropdown.selected_option[0]))
                        conn_baud = int(self.serial_baudrate_textbox.get_text())
                        gvar_ctrl.mcu_serial_object = serial.Serial(port=self.serial_select_dropdown.selected_option[0], baudrate=conn_baud, timeout=.1)
                    except:
                        print("--Connection failed")
                    else:
                        print("--Connected")

                if event.ui_element == self.serial_refresh_button:
                    try:
                        print(self.serial_select_dropdown.options_list)
                        self.serial_select_dropdown.options_list = [('not selected', 'not selected')]
                        ports = serial.tools.list_ports.comports()
                        for port, desc, hwid in sorted(ports):
                                self.serial_select_dropdown.add_options([str(port)])
                    except:
                        print("i don't know why but refresing failed")

                if event.ui_element == self.serial_test_button:
                    print("Test button pressed")
                    

            if (event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED):
                if (event.ui_element == self.test_drop_down):
                    self.check_resolution_changed()
                if (event.ui_element == self.serial_monitor_mode):
                    # ['In app', 'In terminal', 'Disable']
                    if self.serial_monitor_mode.selected_option == 'In app':
                        enable_serial_monitor = 1
                    elif self.serial_monitor_mode.selected_option == 'In terminal':
                        enable_serial_monitor = 2
                    elif self.serial_monitor_mode.selected_option == 'Disable':
                        enable_serial_monitor = 0
                    else:
                        enable_serial_monitor = 0

    def run(self):
        global joysticks
        global enable_serial_monitor
        global serial_msg_text

        global context

        serial_msg_text_size = 200

        while self.running:
            time_delta = self.clock.tick() / 1000.0
            self.time_delta_stack.append(time_delta)
            if len(self.time_delta_stack) > 2000:
                self.time_delta_stack.popleft()
            # check for input
            self.process_events()
            # respond to input
            self.ui_manager.update(time_delta)
            # draw graphics
            self.window_surface.blit(self.background_surface, (0, 0))
            self.ui_manager.draw_ui(self.window_surface)
            pygame.display.update()

            ###change this stuff bc created new serial_handler file^^
    
    """
    class Slider:
        def __init__(self, pos: tuple, size: tuple, initial_val: float, min: int, max: int) -> None:
            self.pos = pos
            self.size = size

            self.slider_left_pos = self.pos[0] - (size[0] // 2)
            self.slider_right_pos = self.pos[0] - (size[0] // 2)
            self.slider_top_pos = self.pos[1] - (size[1] // 2)

            self.min = min
            self.max = max
            self.initial_val = (self.slider_right_pos - self.slider_left_pos) * initial_val


        self.container_rect = pygame.Rect(self.slider_left_pos, self.slider_top_pos, self.size[0], self.size[1])
        self.button_rect = pygame.Rect(self.slider_left_pos + self.initial_val - 5, self.slider_top_pos, 10, self.size[1])

        # label
        self.text = UI.fonts['m'].render(str(int(self.get_value())), True, "white", None)
        self.label_rect = self.text.get_rect(center = (self.pos[0], self.slider_top_pos - 15))
        
        def move_slider(self, mouse_pos):
            pos = mouse_pos[0]
            if pos < self.slider_left_pos:
                pos = self.slider_left_pos
            if pos > self.slider_right_pos:
                pos = self.slider_right_pos
            self.button_rect.centerx = pos

        def hover(self):
            self.hovered = True

        def render(self, app):
            pygame.draw.rect(app.screen, "darkgray", self.container_rect)
            pygame.draw.rect(app.screen, BUTTONSTATES[self.hovered], self.button_rect)
        
        def get_value(self):
            val_range = self.slider_right_pos - self.slider_left_pos - 1
            button_val = self.button_rect.centerx - self.slider_left_pos

            return (button_val/val_range)*(self.max-self.min)+self.min
        
        def display_value(self, app):
            self.text = UI.fonts['m'].render(str(int(self.get_value())), True, "white", None)
            app.screen.blit(self.text, self.label_rect)
    """








