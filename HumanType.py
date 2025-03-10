import time
import random
import pyautogui

pyautogui.PAUSE = 0

# --- ENABLE / DISABLE FEATURES ---
enable_word_pauses = True
enable_sentence_pauses = True
enable_mistyped_chars = True
enable_fix_spelling = True

# Global flag to control typing activity.
typing_active = True

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
    """Backspace 'n' characters with short random delays."""
    for _ in range(n):
        pyautogui.press('backspace')
        time.sleep(random.uniform(0.02, 0.06))

def type_character(char: str, base_delay: float):
    """
    Types a single character with a random delay and a chance for a typo.
    """
    global typing_active, enable_mistyped_chars
    if not typing_active:
        return

    # Apply random delay variation (±30%)
    delay = random.uniform(base_delay * 0.7, base_delay * 1.3)
    pyautogui.typewrite(char)
    time.sleep(delay)

    # Occasionally simulate a typo and fix it
    if enable_mistyped_chars and random.random() < 0.01 and typing_active:
        wrong_char = get_adjacent_char(char)
        pyautogui.typewrite(wrong_char)
        time.sleep(random.uniform(0.3, 0.6))
        pyautogui.press('backspace')
        time.sleep(random.uniform(0.05, 0.1))

    time.sleep(random.uniform(0.02, 0.05))

def type_word(word: str, base_delay: float):
    """Types an individual word character by character."""
    for char in word:
        if not typing_active:
            return
        type_character(char, base_delay)

def mutate_word(word: str, misspell_chance=0.05) -> (str, bool):
    """
    Occasionally misspells the word by randomly replacing, removing, or adding letters.
    Returns a tuple of (final_word, mutated_flag).
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
    Types the provided text with realistic delays, occasional typos, and corrections.
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

if __name__ == "__main__":
    print("Paste the text to type and press Enter:")
    text = input()

    print("Starting in 5 seconds. Make sure your cursor is in the target text field!")
    time.sleep(5)
    type_like_human(text, 320)
