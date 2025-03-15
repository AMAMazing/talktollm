from time import sleep
import win32clipboard
from optimisewait import optimiseWait, set_autopath
import pyautogui
import time
import pywintypes
import base64
import io
from PIL import Image
import importlib.resources
import tempfile
import shutil
import webbrowser
import os

def set_image_path(llm: str, debug: bool = False):
    """Dynamically sets the image path for optimisewait based on package installation location."""
    copy_images_to_temp(llm, debug=debug)

def copy_images_to_temp(llm: str, debug: bool = False):
    """Copies the necessary image files to a temporary directory."""
    temp_dir = tempfile.gettempdir()
    image_path = os.path.join(temp_dir, 'talktollm_images', llm)
    os.makedirs(image_path, exist_ok=True)
    if debug:
        print(f"Temporary image directory: {image_path}")

    # Get the path to the original images directory within the package
    original_images_dir = importlib.resources.files('talktollm').joinpath('images')
    original_image_path = original_images_dir / llm
    if debug:
        print(f"Original image directory: {original_image_path}")
    # Copy each file from the original directory to the temporary directory
    for filename in os.listdir(original_image_path):
        source_file = os.path.join(original_image_path, filename)
        destination_file = os.path.join(image_path, filename)
        if not os.path.exists(destination_file):
            if debug:
                print(f"Copying {source_file} to {destination_file}")
            shutil.copy2(source_file, destination_file)
        elif debug:
            print(f"File already exists: {destination_file}")

    set_autopath(image_path)
    if debug:
        print(f"Autopath set to: {image_path}")

def set_clipboard(text: str, retries: int = 3, delay: float = 0.2):
    for i in range(retries):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            try:
                win32clipboard.SetClipboardText(str(text))
            except Exception:
                # Fallback for Unicode characters
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, str(text).encode('utf-16le'))
            win32clipboard.CloseClipboard()
            return  # Success
        except pywintypes.error as e:
            if e.winerror == 5:  # Access is denied
                print(f"Clipboard access denied. Retrying... (Attempt {i+1}/{retries})")
                time.sleep(delay)
            else:
                raise  # Re-raise other pywintypes errors
        except Exception as e:
            raise  # Re-raise other exceptions
    print(f"Failed to set clipboard after {retries} attempts.")

def talkto(llm: str, prompt: str, imagedata: list[str] | None = None, debug: bool = False, tabswitch: bool = True) -> str:
    """
    Interacts with a specified Large Language Model (LLM).

    Args:
        llm: The name of the LLM to interact with ('deepseek' or 'gemini').
        prompt: The text prompt to send to the LLM.
        imagedata: Optional list of base64 encoded image strings to send to the LLM.
        debug: Whether to enable debugging output.
        tabswitch: Whether to switch tabs after interacting with the LLM.

    Returns:
        The LLM's response as a string.
    """
    llm = llm.lower()
    set_image_path(llm, debug=debug)
    urls = {
        'deepseek': 'https://chat.deepseek.com/',
        'gemini': 'https://aistudio.google.com/prompts/new_chat'
    }

    webbrowser.open_new_tab(urls[llm])

    optimiseWait('message',clicks=2)

    # If there are images, paste each one
    if imagedata:
        for img in imagedata:
            set_clipboard_image(img)
            pyautogui.hotkey('ctrl', 'v')
            sleep(7)  # Ensure upload completes before pasting the next image

    set_clipboard(prompt)
    pyautogui.hotkey('ctrl', 'v')

    sleep(1)

    optimiseWait('run')
    
    optimiseWait('copy')
    
    pyautogui.hotkey('ctrl', 'w')
    
    if tabswitch:
        pyautogui.hotkey('alt', 'tab')

    # Get LLM's response
    win32clipboard.OpenClipboard()
    response = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    return response

def set_clipboard_image(image_data: str, retries: int = 3, delay: float = 0.2):
    """Set image data to clipboard with retries"""
    for attempt in range(retries):
        try:
            binary_data = base64.b64decode(image_data.split(',')[1])
            image = Image.open(io.BytesIO(binary_data))

            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Remove bitmap header
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except pywintypes.error as e:
            if e.winerror == 5:  # Access is denied
                print(f"Clipboard access denied. Retrying... (Attempt {attempt+1}/{retries})")
                time.sleep(delay)
            else:
                raise  # Re-raise other pywintypes errors
        except Exception as e:
            print(f"Error setting image to clipboard: {e}")
            return False
    return False

if __name__ == "__main__":
    print(talkto('gemini','Hi'))