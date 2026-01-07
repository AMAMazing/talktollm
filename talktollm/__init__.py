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
from datetime import datetime, timedelta
from PIL import Image
from time import sleep

# Attempt to import optimisewait
try:
    from optimisewait import optimiseWait, set_autopath
except ImportError:
    print("Warning: 'optimisewait' library not found. Please install it.")
    def set_autopath(path): pass

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
        # Check for local dev folder first
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_source = os.path.join(current_dir, 'images', llm)

        if os.path.isdir(local_source):
            original_path = local_source
            if debug: print(f"DEBUG: Using LOCAL images: {original_path}")
        else:
            # Fallback to installed package resources
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

def talkto(llm: str, prompt: str, imagedata: list[str] | None = None, debug: bool = False, tabswitch: bool = True, cascade: bool = True) -> str:
    """
    Interacts with an LLM via browser. 
    Supports 'cascade' to switch from AI Studio Pro to Flash if rate limited.
    """
    llm = llm.lower()
    
    # URL Mapping
    urls = {
        'deepseek': 'https://chat.deepseek.com/',
        'gemini': 'https://gemini.google.com/app',
        'aistudio': 'https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview',
        'aistudio_flash': 'https://aistudio.google.com/prompts/new_chat?model=gemini-3-flash-preview',
        'nanobanana': 'https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image-preview'
    }

    # 1. CASCADE PRE-CHECK
    # Determine the actual model to use based on persistent rate-limit state
    current_llm_key = llm
    if cascade and llm == 'aistudio':
        if _get_rate_limit_state('aistudio'):
            if debug: print("DEBUG: 'aistudio' (Pro) is currently rate-limited. Cascading to Flash.")
            current_llm_key = 'aistudio_flash'

    if current_llm_key not in urls:
        raise ValueError(f"Unsupported LLM: {llm}")

    # Determine which folder of images to use for UI detection
    img_folder = 'aistudio' if 'aistudio' in current_llm_key or current_llm_key == 'nanobanana' else current_llm_key
    set_image_path(img_folder, debug=debug)

    try:
        if debug: print(f"Opening {current_llm_key}...")
        webbrowser.open_new_tab(urls[current_llm_key])
        sleep(0.5)

        # Wait for the message input area to appear
        optimiseWait(['message','ormessage','type3','message2','typeytype','tyre','typenew', 'typeplz'], 
                     clicks=2, 
                     interrupter=['chrome','aistudio','aistudio2'], 
                     interrupterclicks=[1,0,0])

        # Paste images
        if imagedata:
            for i, img_b64 in enumerate(imagedata):
                if debug: print(f"Pasting image {i+1}...")
                if set_clipboard_image(img_b64):
                    pyautogui.hotkey('ctrl', 'v')
                    sleep(7) # Wait for AI Studio/Gemini upload processing
            sleep(0.5)

        # Paste text prompt
        if debug: print("Pasting prompt...")
        set_clipboard(prompt)
        pyautogui.hotkey('ctrl', 'v')
        sleep(1)
        pyautogui.press('enter')
        pyautogui.hotkey('ctrl', 'enter')

        if current_llm_key == 'gemini':
            optimiseWait('send')

        # Setup clipboard tracking
        set_clipboard('talktollm: awaiting response')
        initial_seq = win32clipboard.GetClipboardSequenceNumber()

        # 2. WAIT FOR COPY OR RATE LIMIT
        if debug: print("Waiting for response (checking for Copy or Rate Limit)...")
        
        # We look for copy buttons OR the rate limit image
        # clicks=0 means don't click yet, just find the image
        search_results = optimiseWait(['copy', 'orcopy', 'copy2', 'copy3', 'cop4', 'copyorsmthn', 'copyimage', 'ratelimit'], 
                                     clicks=0, 
                                     interrupter='scroll')

        # 3. CASCADE TRIGGER (If rate limited during the process)
        if cascade and search_results.get('image') == 'ratelimit' and current_llm_key == 'aistudio':
            if debug: print("DEBUG: Rate limit image detected! Switching to Flash.")
            _set_rate_limit_state('aistudio')
            pyautogui.hotkey('ctrl', 'w') # Close the current limited tab
            sleep(1)
            # RECURSIVE CALL: The pre-check at the top will now pick Flash
            return talkto(llm, prompt, imagedata, debug, tabswitch, cascade)

        # 4. PERFORM ACTUAL COPY
        sleep(1)
        optimiseWait(['copy', 'orcopy','copy2','copy3','cop4','copyorsmthn','copyimage'])
        if debug: print("Copy clicked.")

        # 5. RETRIEVE FROM CLIPBOARD
        start_time = time.time()
        timeout = 20
        response_text = ""
        
        while time.time() - start_time < timeout:
            if win32clipboard.GetClipboardSequenceNumber() != initial_seq:
                content = _get_clipboard_content()
                response_text = content if content is not None else "[Data copied to clipboard]"
                break
            time.sleep(0.2)
        else:
            if debug: print("Timeout: Clipboard never updated.")
            pyautogui.hotkey('ctrl', 'w')
            return ""

        # Cleanup
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
    # Test call
    print(talkto('aistudio', 'Hi, please tell me which model version you are.', debug=True))