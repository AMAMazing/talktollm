import time
import win32clipboard
import pywintypes
import pyautogui
import base64
import io
import json
import tempfile
import shutil
import webbrowser
import os
import importlib.resources
import math
import random
import threading
from datetime import datetime, timedelta
from PIL import Image
from time import sleep

# --- Imports from optimisewait with full backward compatibility ---
try:
    from optimisewait import optimiseWait, set_autopath, wind_mouse, humancircles
except ImportError:
    try:
        from optimisewait import optimiseWait, set_autopath, wind_mouse, organic_trackpad_swirl as humancircles
    except ImportError:
        try:
            from optimisewait import optimiseWait, set_autopath, wind_mouse
            def humancircles(duration=2.0, *args, **kwargs):
                time.sleep(duration)
        except ImportError:
            print("Warning: 'optimisewait' library not found. Please install it.")
            def set_autopath(path): pass
            def optimiseWait(*args, **kwargs): return {'found': False}
            def wind_mouse(sx, sy, dx, dy, *args, **kwargs): pyautogui.moveTo(dx, dy)
            def humancircles(duration=2.0, *args, **kwargs): time.sleep(duration)

# Backward compatibility alias
organic_trackpad_swirl = humancircles

# Backward compatibility wrappers for any external scripts importing old talktollm internals
def _perform_windmouse_move(dest_x, dest_y):
    curr_x, curr_y = pyautogui.position()
    wind_mouse(curr_x, curr_y, dest_x, dest_y)

def _perform_human_circles(duration=2.0):
    humancircles(duration=duration)

# Constants
STATE_FILE = os.path.join(os.path.expanduser("~"), ".talktollm_state.json")

# --- Persistence Logic for Rate Limiting ---

def _get_rate_limit_state(llm: str) -> bool:
    """Checks if the specific LLM is currently marked as rate-limited (within 1 hour)."""
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            limit_time_str = data.get(llm)
            if limit_time_str:
                limit_time = datetime.fromisoformat(limit_time_str)
                # If the limit happened less than 60 minutes ago, it's still active
                if datetime.now() < limit_time + timedelta(hours=1):
                    return True
    except Exception:
        pass
    return False

def _set_rate_limit_state(llm: str):
    """Saves the current timestamp to the state file for the specified LLM."""
    data = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
        except: pass

    data[llm] = datetime.now().isoformat()
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving state file: {e}")

# --- Image and Resource Setup ---

def set_image_path(llm: str, debug: bool = False):
    """Dynamically sets the image path for optimisewait."""
    copy_images_to_temp(llm, debug=debug)

def copy_images_to_temp(llm: str, debug: bool = False):
    """Copies image files to a temp directory, prioritizing local dev files."""
    temp_dir = tempfile.gettempdir()
    image_path = os.path.join(temp_dir, 'talktollm_images', llm)

    shutil.rmtree(image_path, ignore_errors=True)
    os.makedirs(image_path, exist_ok=True)

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_source = os.path.join(current_dir, 'images', llm)

        if os.path.isdir(local_source):
            original_path = local_source
            if debug: print(f"DEBUG: Using LOCAL images: {original_path}")
        else:
            res = importlib.resources.files('talktollm').joinpath('images')
            original_path = str(res / llm)
            if debug: print(f"DEBUG: Using INSTALLED images: {original_path}")

        if not os.path.exists(original_path):
             set_autopath(image_path)
             return

        for filename in os.listdir(original_path):
            src = os.path.join(original_path, filename)
            dst = os.path.join(image_path, filename)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

        set_autopath(image_path)
        if debug: print(f"Autopath set to: {image_path}")

    except Exception as e:
        print(f"Error during image setup: {e}")
        set_autopath(image_path)

# --- Interface Detection Helper ---

def _is_interface_detected(img_folder: str, debug: bool = False) -> bool:
    """
    Checks whether the LLM chat interface is already visible on the screen.
    Looks for standard input indicator images in the temporary image directory.
    """
    try:
        temp_dir = tempfile.gettempdir()
        target_dir = os.path.join(temp_dir, 'talktollm_images', img_folder)

        if not os.path.exists(target_dir):
            copy_images_to_temp(img_folder, debug=debug)

        if not os.path.exists(target_dir):
            if debug: print(f"DEBUG: Image folder not found: {target_dir}")
            return False

        input_candidates = ['message', 'ormessage', 'type3', 'message2', 'typeytype', 'tyre', 'typenew', 'typeplz', 'starttype', 'ask']

        available_files = {}
        for fname in os.listdir(target_dir):
            base_name, _ = os.path.splitext(fname)
            available_files[base_name] = os.path.join(target_dir, fname)

        for candidate in input_candidates:
            img_path = available_files.get(candidate)
            if not img_path:
                candidate_png = os.path.join(target_dir, f"{candidate}.png")
                if os.path.isfile(candidate_png):
                    img_path = candidate_png

            if img_path and os.path.isfile(img_path):
                try:
                    pos = pyautogui.locateOnScreen(img_path, confidence=0.8)
                except (TypeError, Exception):
                    try:
                        pos = pyautogui.locateOnScreen(img_path)
                    except Exception:
                        pos = None

                if pos is not None:
                    if debug: print(f"DEBUG: Interface detected on screen using '{candidate}' at {pos}.")
                    return True

    except Exception as e:
        if debug: print(f"DEBUG: Error checking interface detection: {e}")

    return False

# --- Background Tab Reset Helper (Option A) ---

def _background_reset(url: str, tabswitch: bool):
    """
    Closes the used tab, pre-opens a fresh session tab in the background,
    and optionally executes alt+tab.
    """
    try:
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.3)
        webbrowser.open_new_tab(url)
        time.sleep(0.5)
        if tabswitch:
            pyautogui.hotkey('alt', 'tab')
    except Exception as e:
        print(f"Error in _background_reset: {e}")

# --- Clipboard Helpers ---

def set_clipboard(text: str, retries: int = 5, delay: float = 0.2):
    for i in range(retries):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(str(text), win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return
        except pywintypes.error:
            try: win32clipboard.CloseClipboard()
            except: pass
            time.sleep(delay)

def set_clipboard_image(image_data: str, retries: int = 5, delay: float = 0.2):
    try:
        binary_data = base64.b64decode(image_data.split(',', 1)[1])
        image = Image.open(io.BytesIO(binary_data))
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
    except Exception as e:
        print(f"Image processing error: {e}")
        return False

    for attempt in range(retries):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except pywintypes.error:
            try: win32clipboard.CloseClipboard()
            except: pass
            time.sleep(delay)
    return False

def _get_clipboard_content(retries: int = 3, delay: float = 0.2) -> str | None:
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            response = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return response
        except:
            try: win32clipboard.CloseClipboard()
            except: pass
            time.sleep(delay)
    return None

# --- Main Interaction Logic ---

def talkto(llm: str, prompt: str, imagedata: list[str] | None = None, debug: bool = False, tabswitch: bool = True, cascade: bool = True, humanize: bool = False, windmouse: bool = False, fast_mode: bool = False) -> str:
    """
    Interacts with an LLM via browser.
    Supports 'cascade' to switch through models if rate limited.
    Chain: Pro > Flash -> Flash Lite
    Supports 'fast_mode' to eliminate cold browser launch and tab reset latency.
    """
    llm = llm.lower()

    # --- Backwards Compatibility Mapping ---
    legacy_mapping = {
        'aistudio': 'aistudio-pro',
        'aistudio_flash': 'aistudio-flash',
        'gemini-3.1-flash-lite-preview': 'aistudio-flash-lite'
    }
    llm = legacy_mapping.get(llm, llm)

    # URL Mapping
    urls = {
        'deepseek': 'https://chat.deepseek.com/',
        'gemini': 'https://gemini.google.com/app',
        'aistudio-pro': 'https://aistudio.google.com/prompts/new_chat?model=gemini-pro-latest',
        'aistudio-flash': 'https://aistudio.google.com/prompts/new_chat?model=gemini-flash-latest',
        'aistudio-flash-lite': 'https://aistudio.google.com/prompts/new_chat?model=gemini-flash-lite-latest',
        'nanobanana': 'https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image-preview'
    }

    # Define the fallback priority chain
    CASCADE_CHAIN = ['aistudio-pro', 'aistudio-flash', 'aistudio-flash-lite']

    # 1. CASCADE PRE-CHECK
    current_llm_key = llm

    if cascade and llm in CASCADE_CHAIN:
        try:
            start_index = CASCADE_CHAIN.index(llm)
        except ValueError:
            start_index = 0

        for i in range(start_index, len(CASCADE_CHAIN)):
            candidate = CASCADE_CHAIN[i]
            if _get_rate_limit_state(candidate):
                if debug: print(f"DEBUG: '{candidate}' is rate-limited. Checking next fallback...")
                continue
            else:
                current_llm_key = candidate
                if debug and current_llm_key != llm:
                    print(f"DEBUG: Cascaded to '{current_llm_key}'")
                break

        if _get_rate_limit_state(current_llm_key):
             print("WARNING: All models in cascade chain appear to be rate limited. Trying last resort.")

    if current_llm_key not in urls:
        raise ValueError(f"Unsupported LLM: {llm}")

    if current_llm_key in CASCADE_CHAIN or current_llm_key == 'nanobanana':
        img_folder = 'aistudio'
    else:
        img_folder = current_llm_key

    set_image_path(img_folder, debug=debug)

    active_humanize = False if fast_mode else humanize
    active_windmouse = False if fast_mode else windmouse

    try:
        is_already_open = False
        if fast_mode:
            is_already_open = _is_interface_detected(img_folder, debug=debug)

        if not is_already_open:
            if debug: print(f"Opening {current_llm_key}...")
            webbrowser.open_new_tab(urls[current_llm_key])
            sleep(1.5)
        else:
            if debug: print(f"DEBUG: Interface already open for {current_llm_key}. Skipping tab launch.")

        # Wait for the message input area to appear
        optimiseWait(['message','ormessage','type3','message2','typeytype','tyre','typenew', 'typeplz','starttype', 'ask'],
                     clicks=2,
                     interrupter=['chrome','aistudio','aistudio2'],
                     interrupterclicks=[1,0,0],
                     humanize=active_humanize)

        # Paste images
        if imagedata:
            for i, img_b64 in enumerate(imagedata):
                if debug: print(f"Pasting image {i+1}...")
                if set_clipboard_image(img_b64):
                    pyautogui.hotkey('ctrl', 'v')
            if llm == 'gemini':
                sleep(5)
            else:
                sleep(0.5)

        # Paste text prompt
        if debug: print("Pasting prompt...")
        set_clipboard(prompt)
        pyautogui.hotkey('ctrl', 'v')
        sleep(0.2 if fast_mode else 1)
        pyautogui.press('enter')
        pyautogui.hotkey('ctrl', 'enter')

        # Setup clipboard tracking
        set_clipboard('talktollm: awaiting response')
        initial_seq = win32clipboard.GetClipboardSequenceNumber()

        # Execute natural idle movements (WindMouse + Trackpad Swirl)
        if active_windmouse:
            if debug: print("Performing natural idle movements (WindMouse & HumanCircles)...")
            screen_w, screen_h = pyautogui.size()

            pad = 250
            target_x = random.randint(pad, max(pad + 1, screen_w - pad))
            target_y = random.randint(pad, max(pad + 1, screen_h - pad))

            try:
                curr_x, curr_y = pyautogui.position()
                wind_mouse(curr_x, curr_y, target_x, target_y)
                humancircles(duration=random.uniform(1.8, 3.2))
            except Exception as e:
                if debug: print(f"Idle mouse movement failed: {e}")

        # 2. WAIT FOR COPY OR RATE LIMIT
        if debug: print("Waiting for response (checking for Copy or Rate Limit)...")

        search_results = optimiseWait(['copy', 'orcopy', 'copy2', 'copy3', 'cop4', 'copyorsmthn', 'copyimage', 'ratelimit','copyyy','copyy'],
                                     clicks=0,
                                     interrupter='scroll',
                                     humanize=active_humanize)

        # 3. CASCADE TRIGGER
        if cascade and search_results.get('image') == 'ratelimit' and current_llm_key in CASCADE_CHAIN:
            if debug: print(f"DEBUG: Rate limit detected on {current_llm_key}! Switching to next fallback.")
            _set_rate_limit_state(current_llm_key)
            pyautogui.hotkey('ctrl', 'w')
            sleep(1)
            return talkto(llm, prompt, imagedata, debug, tabswitch, cascade, humanize, windmouse, fast_mode)

        # 4. PERFORM ACTUAL COPY
        sleep(0.2 if fast_mode else 1)
        optimiseWait(['copy', 'orcopy','copy2','copy3','cop4','copyorsmthn','copyimage','copyyy','copyy'], humanize=active_humanize)
        if debug: print("Copy clicked.")

        # 5. RETRIEVE FROM CLIPBOARD
        start_time = time.time()
        timeout = 20
        response_text = ""

        poll_interval = 0.05 if fast_mode else 0.2

        while time.time() - start_time < timeout:
            if win32clipboard.GetClipboardSequenceNumber() != initial_seq:
                content = _get_clipboard_content()
                response_text = content if content is not None else "[Data copied to clipboard]"
                break
            time.sleep(poll_interval)
        else:
            if debug: print("Timeout: Clipboard never updated.")
            pyautogui.hotkey('ctrl', 'w')
            return ""

        if fast_mode:
            if debug: print("Spawning background tab reset thread and returning immediately.")
            threading.Thread(
                target=_background_reset,
                args=(urls[current_llm_key], tabswitch),
                daemon=True
            ).start()
            return response_text

        # Synchronous cleanup for standard mode
        if debug: print("Closing tab and finishing.")
        pyautogui.hotkey('ctrl', 'w')
        sleep(0.5)
        if tabswitch:
            pyautogui.hotkey('alt', 'tab')

        return response_text

    except Exception as e:
        print(f"Critical Error in talkto: {e}")
        try: win32clipboard.CloseClipboard()
        except: pass
        return ""

if __name__ == "__main__":
    print(talkto('gemini', 'Hi', debug=True, humanize=True, windmouse=True))