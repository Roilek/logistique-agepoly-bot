import time

import pyautogui

item_pos = (736, 233)


def remove_events(n: int = 1) -> None:
    pyautogui.hotkey('ctrl', 'left', interval=0.1)
    time.sleep(0.25)
    pyautogui.click(item_pos)
    for i in range(n):
        pyautogui.hotkey('delete', interval=0.2)
    pyautogui.hotkey('ctrl', 'right', interval=0.1)
    return


def get_position() -> None:
    print(pyautogui.position())
    return


if __name__ == '__main__':
    get_position()
    remove_events(40)
