import keyboard
from art import tprint
tprint('SnapTap')
print('Version 1.0')
print('GitHub > https://github.com/ErkinKraft')
# Переменные для хранения состояния направления
current_direction = None


def on_direction(direction):
    global current_direction

    # Если текущее направление совпадает с новым, ничего не делаем
    if current_direction == direction:
        return

    # Если текущее направление противоположно новому, отжимаем текущее направление
    if (current_direction == 'left' and direction == 'right'):
        simulate_key_release('left')  # Отпускаем 'left'

    if (current_direction == 'right' and direction == 'left'):
        simulate_key_release('right')  # Отпускаем 'right'

    # Устанавливаем новое направление
    current_direction = direction



    simulate_key_press(direction)  # Имитация нажатия нового направления


def release_direction(direction):
    global current_direction

    # Если отпущенное направление совпадает с текущим, сбрасываем текущее направление
    if direction == current_direction:

        simulate_key_release(current_direction)  # Имитация отпускания
        # Если отпущено 'left', проверяем, не нажата ли 'right'
        if current_direction == 'left':
            current_direction = None  # Сброс текущего направления
        elif current_direction == 'right':
            current_direction = 'right'  # Сохраняем 'right' как текущее направление


def simulate_key_press(direction):
    if direction == 'left':
        keyboard.press('a')
    elif direction == 'right':
        keyboard.press('d')
    elif direction == 'up':
        keyboard.press('w')
    elif direction == 'down':
        keyboard.press('s')


def simulate_key_release(direction):
    if direction == 'left':
        keyboard.release('a')
    elif direction == 'right':
        keyboard.release('d')
    elif direction == 'up':
        keyboard.release('w')
    elif direction == 'down':
        keyboard.release('s')





def start_snap_tap_mode():


    # Привязываем клавиши к функциям
    keyboard.on_press_key('a', lambda _: on_direction('left'))
    keyboard.on_press_key('d', lambda _: on_direction('right'))
    keyboard.on_press_key('w', lambda _: on_direction('up'))
    keyboard.on_press_key('s', lambda _: on_direction('down'))

    # Привязываем отпускание клавиш к функции
    keyboard.on_release_key('a', lambda _: release_direction('left'))
    keyboard.on_release_key('d', lambda _: release_direction('right'))
    keyboard.on_release_key('w', lambda _: release_direction('up'))
    keyboard.on_release_key('s', lambda _: release_direction('down'))

    # Ожидание завершения программы
    keyboard.wait('f9')  # Нажмите 'f9' для выхода


# Основная логика программы
if __name__ == "__main__":
    command = input("Введите команду (start): ")
    if command.lower() == "start":
        print('SnapTap Активен')
        print('Для отключения функции SnapTap нажмите F9')
        start_snap_tap_mode()
    else:
        print("Неизвестная команда.")
