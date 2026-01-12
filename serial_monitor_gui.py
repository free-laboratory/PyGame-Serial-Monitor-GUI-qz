# MATPLOTLIB VErSION -- won't run
# 
# import os
# import re
# import time
# import multiprocessing as mp

# import serial
# import serial.tools.list_ports

# import gvar_ctrl
# import gui


# def open_serial_log(log_path="./serial_log"):
#     """
#     Open a new serial log file with an incremented index.
#     Creates the directory if it doesn't exist.
#     """
#     try:
#         dir_list = os.listdir(log_path)
#     except Exception as e:
#         print("open_serial_log: ", e)
#         print("Creating a folder with name " + log_path)
#         os.mkdir(log_path)
#         dir_list = os.listdir(log_path)

#     dir_list = [f for f in dir_list if os.path.isfile(os.path.join(log_path, f))]

#     largest_index = 0
#     for each_log in dir_list:
#         # extract first integer from filename
#         temp = re.findall(r"\d+", each_log)
#         if not temp:
#             continue
#         res = list(map(int, temp))
#         largest_index = max(largest_index, res[0])

#     log_name = f"serial_log_{largest_index + 1}.txt"
#     full_path = os.path.join(log_path, log_name)
#     gvar_ctrl.serial_log_file = open(full_path, "w")
#     print(f"Logging serial to: {full_path}")


# def mp_plot_process(shared_values):
#     print("Plot process starting...", flush=True)

#     import matplotlib
#     matplotlib.use("Qt5Agg") 
#     import matplotlib.pyplot as plt

#     plt.ion()
#     fig, ax = plt.subplots()
#     try:
#         fig.canvas.manager.set_window_title("Slider Values Plot")
#     except Exception:
#         pass  # some backends don't support this

#     n = len(shared_values)
#     x = list(range(1, n + 1))

#     bars = ax.bar(x, list(shared_values))
#     ax.set_ylim(0, 100)
#     ax.set_xlabel("Slider index")
#     ax.set_ylabel("Value (1–100)")
#     ax.set_title("Live values from Pygame sliders")

#     # Show the window
#     plt.show(block=False)

#     while True:
#         try:
#             vals = list(shared_values)
#             for bar, v in zip(bars, vals):
#                 bar.set_height(v)

#             # keep a bit of headroom
#             ax.set_ylim(0, max(100, max(vals) + 5))
#             fig.canvas.draw_idle()
#             plt.pause(0.1)
#         except Exception as e:
#             print("Plot process error:", e, flush=True)
#             break


# if __name__ == "__main__":
#     # On macOS, 'fork' usually plays nicer with GUI stuff
#     try:
#         mp.set_start_method("fork")
#     except RuntimeError:
#         # Start method already set in this interpreter session
#         pass

#     with mp.Manager() as manager:
#         # Shared list of 12 slider values, init at 50
#         shared_values = manager.list([50.0] * 12)

#         # Start ONLY the plot in a separate process
#         plot_process = mp.Process(target=mp_plot_process, args=(shared_values,))
#         plot_process.start()

#         # Run Pygame GUI in the main process (more reliable)
#         try:
#             ports = serial.tools.list_ports.comports()
#             open_serial_log()
#             print("Available serial ports:")
#             for port, desc, hwid in sorted(ports):
#                 print(f"{port}: [{hwid}]  {desc}")

#             app = gui.OptionsUIApp(shared_values=shared_values)
#             app.run()
#         finally:
#             print("Main: shutting down plot process...")
#             plot_process.terminate()
#             plot_process.join()

import os
import re
import time
import multiprocessing as mp

import serial
import serial.tools.list_ports

import gvar_ctrl
import gui

import matplotlib.pyplot as plt
import numpy as np

def open_serial_log(log_path="./serial_log"):
    try:
        dir_list = os.listdir(log_path)
    except Exception as e:
        print("open_serial_log: ", e)
        print("Creating a folder with name " + log_path)
        os.mkdir(log_path)
        dir_list = os.listdir(log_path)

    dir_list = [f for f in dir_list if os.path.isfile(os.path.join(log_path, f))]

    largest_index = 0
    for each_log in dir_list:
        temp = re.findall(r"\d+", each_log)
        if not temp:
            continue
        res = list(map(int, temp))
        largest_index = max(largest_index, res[0])

    log_name = f"serial_log_{largest_index + 1}.txt"
    full_path = os.path.join(log_path, log_name)
    gvar_ctrl.serial_log_file = open(full_path, "w")
    print(f"Logging serial to: {full_path}")


def mp_plot_process(shared_values):
    import pygame
    os.environ["SDL_VIDEO_WINDOW_POS"] = "%d,%d" % (750, 100)

    pygame.init()
    pygame.display.set_caption("Slider Values Plot (Pygame)")

    W, H = 600, 400
    screen = pygame.display.set_mode((W, H))
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 24)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        try:
            values = list(shared_values)
        except Exception:
            values = []

        screen.fill((15, 15, 30))

        if values:
            n = len(values)
            max_val = max(max(values), 1.0)

            # Bar dimensions
            margin_x = 40
            margin_y = 40
            usable_w = W - 2 * margin_x
            usable_h = H - 2 * margin_y

            bar_width = usable_w / max(n, 1)

            for i, v in enumerate(values):
                h = (v / max_val) * usable_h
                x = margin_x + i * bar_width
                y = H - margin_y - h

                rect = pygame.Rect(int(x + 4), int(y), int(bar_width - 8), int(h))
                pygame.draw.rect(screen, (80, 180, 255), rect)
                pygame.draw.rect(screen, (200, 200, 255), rect, 1)

                label = font.render(str(i + 1), True, (230, 230, 230))
                label_rect = label.get_rect(center=(rect.centerx, H - margin_y / 2))
                screen.blit(label, label_rect)

            title = font.render("Slider Values", True, (240, 240, 240))
            title_rect = title.get_rect(center=(W // 2, margin_y / 2))
            screen.blit(title, title_rect)

        pygame.display.flip()

    pygame.quit()

def test_process(shared_values):
    # generate a test dummy process that use matplotlib to plot some randome data
    # generate a bar plot to plot the values in shared_values
    import matplotlib.pyplot as plt
    import numpy as np

    plt.ion()
    fig, ax = plt.subplots()
    try:
        fig.canvas.manager.set_window_title("Test Slider Values Plot")
    except Exception:
        pass  # some backends don't support this
    n = len(shared_values)
    x = list(range(1, n + 1))
    bars = ax.bar(x, list(shared_values))
    ax.set_ylim(0, 100)
    ax.set_xlabel("Slider index")
    ax.set_ylabel("Value (1–100)")
    ax.set_title("Test Live values from Pygame sliders")
    plt.show(block=False)
    
    while True:
        try:
            vals = list(shared_values)
            for bar, v in zip(bars, vals):
                bar.set_height(v)

            # keep a bit of headroom
            ax.set_ylim(0, max(100, max(vals) + 5))
            fig.canvas.draw_idle()
            plt.pause(0.1)
        except Exception as e:
            print("Test Plot process error:", e, flush=True)
            break

#to open the second window
if __name__ == "__main__":
    


    try:
        mp.set_start_method("spawn")
    except RuntimeError:
        pass

    with mp.Manager() as manager:
        shared_values = manager.list([50.0] * 12)

        plot_process = mp.Process(target=mp_plot_process, args=(shared_values,))
        plot_process.start()

        another_process = mp.Process(target=test_process, args=(shared_values,))
        another_process.start()

        try:
            ports = serial.tools.list_ports.comports()
            open_serial_log()
            print("Available serial ports:")
            for port, desc, hwid in sorted(ports):
                print(f"{port}: [{hwid}]  {desc}")

            app = gui.OptionsUIApp(shared_values=shared_values)
            app.run()
        finally:
            print("Main: shutting down plot process...")
            plot_process.terminate()
            another_process.terminate()
            another_process.join()
            plot_process.join()
