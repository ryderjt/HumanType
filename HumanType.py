import time
import random
import threading
import pyautogui
import pyperclip
from pynput import keyboard

pyautogui.PAUSE = 0

# --- ENABLE / DISABLE FEATURES ---
enable_word_pauses = True
enable_sentence_pauses = True
enable_mistyped_chars = True
enable_fix_spelling = True

typing_active = False
typing_thread = None

QWERTY_ADJACENCY = {
    'a': ['s'],
    'b': ['v', 'n'],
    'c': ['x', 'v'],
    'd': ['s', 'f'],
    'e': ['w', 'r'],
    'f': ['d', 'g'],
    'g': ['f', 'h'],
    'h': ['g', 'j'],
    'i': ['u', 'o'],
    'j': ['h', 'k'],
    'k': ['j', 'l'],
    'l': ['k'],
    'm': ['n'],
    'n': ['b', 'm'],
    'o': ['i', 'p'],
    'p': ['o'],
    'q': ['w'],
    'r': ['e', 't'],
    's': ['a', 'd'],
    't': ['r', 'y'],
    'u': ['y', 'i'],
    'v': ['c', 'b'],
    'w': ['q', 'e'],
    'x': ['z', 'c'],
    'y': ['t', 'u'],
    'z': ['x'],
}

def get_adjacent_char(char: str) -> str:
    """
    Return a 'close' QWERTY neighbor to char if possible.
    If no adjacency found, falls back to returning the same character.
    Maintains case if original is uppercase.
    """
    is_upper = char.isupper()
    base_char = char.lower()

    if base_char in QWERTY_ADJACENCY:
        neighbors = QWERTY_ADJACENCY[base_char]
        if neighbors:
            wrong = random.choice(neighbors)
            return wrong.upper() if is_upper else wrong
    return char

def backspace_n_chars(n):
    """Helper to backspace 'n' characters with short random delays."""
    for _ in range(n):
        pyautogui.press('backspace')
        time.sleep(random.uniform(0.02, 0.06))

def type_character(char: str, base_delay: float):
    """
    Types a single character with:
      - Random delay around the base (±30%).
      - ~1% chance of a single-character typo that is corrected immediately.
      - A small extra pause after each typed character to appear more human.
    """
    global typing_active, enable_mistyped_chars
    if not typing_active:
        return

    # RANDOM VARIATION ±30%
    delay = random.uniform(base_delay * 0.7, base_delay * 1.3)

    pyautogui.typewrite(char)
    time.sleep(delay)

    if enable_mistyped_chars and random.random() < 0.01 and typing_active:
        wrong_char = get_adjacent_char(char)
        pyautogui.typewrite(wrong_char)

        time.sleep(random.uniform(0.3, 0.6))

        pyautogui.press('backspace')
        time.sleep(random.uniform(0.05, 0.1))

    time.sleep(random.uniform(0.02, 0.05))

def type_word(word: str, base_delay: float):
    """Types an individual word (character by character)."""
    for char in word:
        if not typing_active:
            return
        type_character(char, base_delay)

def mutate_word(word: str, misspell_chance=0.05) -> (str, bool):
    """
    With a small chance, 'misspell' the entire word by
    randomly replacing, removing, or adding letters.
    Returns (final_word, mutated_flag).
    """
    original = word.strip()
    if not original or random.random() >= misspell_chance:
        return original, False

    letters = list(original)
    edits = random.randint(1, 2)
    for _ in range(edits):
        if not letters:
            break
        op = random.choice(["replace", "remove", "add"])
        if op == "replace":
            idx = random.randrange(len(letters))
            letters[idx] = random.choice("abcdefghijklmnopqrstuvwxyz")
        elif op == "remove":
            idx = random.randrange(len(letters))
            del letters[idx]
        elif op == "add":
            idx = random.randrange(len(letters) + 1)
            letters.insert(idx, random.choice("abcdefghijklmnopqrstuvwxyz"))

    mutated = "".join(letters)
    return mutated, (mutated != original)

def type_like_human(text, base_wpm=320):
    """
    Types 'text' with:
      - A faster base WPM (320).
      - Occasional entire-word misspelling, immediately fixed.
      - Single-character typos with immediate fix.
      - Highly varied (and sometimes zero) pause between words.
      - Up to 4s pause after sentence punctuation.
    """
    global typing_active

    avg_chars_per_second = (base_wpm * 5) / 60.0
    base_delay = 1.0 / avg_chars_per_second

    current_word_chars = []
    i = 0
    while i < len(text) and typing_active:
        char = text[i]

        if char.isalnum():
            current_word_chars.append(char)
        else:
            if current_word_chars:
                original_word = "".join(current_word_chars)
                final_word, was_mutated = mutate_word(original_word, misspell_chance=0.05)

                type_word(final_word, base_delay)

                if enable_fix_spelling and was_mutated and typing_active:
                    time.sleep(random.uniform(0.2, 0.8))
                    backspace_n_chars(len(final_word))
                    type_word(original_word, base_delay)

                current_word_chars = []

            if typing_active:
                type_character(char, base_delay)

                if enable_word_pauses and char == ' ' and typing_active:
                    if random.random() < 0.8:
                        time.sleep(random.uniform(0.0, 0.15))
                    else:
                        time.sleep(random.uniform(0.5, 2.0))

                if enable_sentence_pauses and char in ".?!" and typing_active:
                    time.sleep(random.uniform(0, 4.0))

        i += 1

    if current_word_chars and typing_active:
        original_word = "".join(current_word_chars)
        final_word, was_mutated = mutate_word(original_word, misspell_chance=0.05)
        type_word(final_word, base_delay)
        if enable_fix_spelling and was_mutated and typing_active:
            time.sleep(random.uniform(0.2, 0.8))
            backspace_n_chars(len(final_word))
            type_word(original_word, base_delay)

    print("[INFO] Done typing (or stopped).")
    typing_active = False

# --- HOTKEY BEHAVIOR ---

def on_activate_start():
    """
    Hotkey: Ctrl+Shift+I
    1) Wait 2 seconds
    2) Get the clipboard
    3) Start typing in a separate thread
    """
    global typing_active, typing_thread
    if typing_active and typing_thread and typing_thread.is_alive():
        print("[INFO] Already typing. Press Ctrl+Shift+O to stop first.")
        return

    typing_active = True
    print("[INFO] Start hotkey pressed; waiting 2 seconds...")
    time.sleep(2.0)

    if not typing_active:
        print("[INFO] Typing canceled before it started.")
        return

    text = pyperclip.paste()
    if not text:
        print("[INFO] Clipboard is empty. Copy something first!")
        typing_active = False
        return

    print("[INFO] Beginning to type from clipboard...")
    typing_thread = threading.Thread(target=type_like_human, args=(text, 320))
    typing_thread.start()

def on_activate_stop():
    """Hotkey: Ctrl+Shift+O - Stop typing immediately."""
    global typing_active
    if typing_active:
        print("[INFO] Stop hotkey pressed. Stopping typing now.")
        typing_active = False
    else:
        print("[INFO] Not currently typing.")

start_hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+<shift>+i'),
    on_activate_start
)
stop_hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+<shift>+o'),
    on_activate_stop
)

def on_press(key):
    start_hotkey.press(listener.canonical(key))
    stop_hotkey.press(listener.canonical(key))

def on_release(key):
    start_hotkey.release(listener.canonical(key))
    stop_hotkey.release(listener.canonical(key))

if __name__ == "__main__":
    print("Now listening for hotkeys:")
    print("  - Ctrl+Shift+I to start (waits 2s, then types)")
    print("  - Ctrl+Shift+O to stop immediately")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()