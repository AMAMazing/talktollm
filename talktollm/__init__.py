# talktollm/__init__.py

import time
import win32clipboard
import pywintypes
import pyautogui
import base64
import io
from PIL import Image
import importlib.resources
import tempfile
import shutil
import webbrowser
import os
from time import sleep # Explicitly import sleep if not already done

# Assuming optimisewait is correctly installed and available
try:
    from optimisewait import optimiseWait, set_autopath
except ImportError:
    print("Warning: 'optimisewait' library not found. Please install it.")
    # Define dummy functions if optimisewait is not installed to avoid NameErrors
    # You might want to raise an error or handle this differently
    def set_autopath(path):
        print(f"set_autopath called with '{path}' (dummy function).")


def set_image_path(llm: str, debug: bool = False):
    """Dynamically sets the image path for optimisewait based on package installation location."""
    copy_images_to_temp(llm, debug=debug)

def copy_images_to_temp(llm: str, debug: bool = False):
    """
    Copies the necessary image files to a temporary directory, ensuring a clean state.
    """
    temp_dir = tempfile.gettempdir()
    image_path = os.path.join(temp_dir, 'talktollm_images', llm)

    # Clean up the directory before use to ensure a pristine state
    shutil.rmtree(image_path, ignore_errors=True)
    os.makedirs(image_path, exist_ok=True)
    
    if debug:
        print(f"Cleaned and prepared temporary image directory: {image_path}")

    try:
        # Get the path to the original images directory within the package
        original_images_dir = importlib.resources.files('talktollm').joinpath('images')
        original_image_path = original_images_dir / llm
        if debug:
            print(f"Original image directory: {original_image_path}")

        # Check if the source directory exists before trying to list its contents
        if not os.path.isdir(original_image_path):
             print(f"Warning: Original image directory not found: {original_image_path}")
             # Set autopath to the potentially empty temp dir anyway, or handle error
             set_autopath(image_path)
             if debug:
                 print(f"Autopath set to potentially empty dir: {image_path}")
             return

        # Copy each file from the original directory to the temporary directory
        for filename in os.listdir(original_image_path):
            source_file = os.path.join(original_image_path, filename)
            destination_file = os.path.join(image_path, filename)
            # Ensure it's a file before copying
            if os.path.isfile(source_file):
                if not os.path.exists(destination_file) or os.path.getmtime(source_file) > os.path.getmtime(destination_file):
                    if debug:
                        print(f"Copying {source_file} to {destination_file}")
                    shutil.copy2(source_file, destination_file)
                elif debug:
                    print(f"File already exists and is up-to-date: {destination_file}")
            elif debug:
                 print(f"Skipping non-file item: {source_file}")

        set_autopath(image_path)
        if debug:
            print(f"Autopath set to: {image_path}")

    except FileNotFoundError:
        print(f"Error: Could not find the 'talktollm' package resources. Ensure it's installed correctly.")
        # Handle error appropriately, maybe raise it or set a default path
        set_autopath(image_path) # Try setting path anyway
    except Exception as e:
        print(f"An unexpected error occurred during image setup: {e}")
        set_autopath(image_path) # Try setting path anyway


def set_clipboard(text: str, retries: int = 5, delay: float = 0.2):
    """Sets text to the clipboard with retry logic for Access Denied errors."""
    for i in range(retries):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            # Use SetClipboardText with appropriate encoding handling
            win32clipboard.SetClipboardText(str(text), win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            # print(f"Debug: Clipboard set successfully on attempt {i+1}") # Optional debug
            return  # Success
        except pywintypes.error as e:
            # error: (5, 'OpenClipboard', 'Access is denied.')
            # error: (1418, 'SetClipboardData', 'The thread does not have open clipboard.') - might happen if Open failed
            if e.winerror == 5 or e.winerror == 1418:
                # print(f"Clipboard access denied/error setting text. Retrying... (Attempt {i+1}/{retries})") # Optional debug
                try:
                    # Ensure clipboard is closed if OpenClipboard succeeded but subsequent calls failed
                    win32clipboard.CloseClipboard()
                except pywintypes.error:
                    pass # Ignore error if closing failed (it might not have been opened)
                time.sleep(delay)
            else:
                print(f"Unexpected pywintypes error setting clipboard text: {e}")
                try:
                    win32clipboard.CloseClipboard()
                except pywintypes.error:
                    pass
                raise  # Re-raise other pywintypes errors
        except Exception as e:
            print(f"Unexpected error setting clipboard text: {e}")
            try:
                win32clipboard.CloseClipboard()
            except pywintypes.error:
                pass
            raise  # Re-raise other exceptions
    print(f"Failed to set clipboard text after {retries} attempts.")
    # Consider raising an exception here if clipboard setting is critical
    # raise RuntimeError(f"Failed to set clipboard text after {retries} attempts.")

def set_clipboard_image(image_data: str, retries: int = 5, delay: float = 0.2):
    """Sets image data (base64) to the clipboard with retry logic."""
    image = None
    try:
        # Decode base64 only once
        binary_data = base64.b64decode(image_data.split(',', 1)[1]) # Use split with maxsplit=1
        image = Image.open(io.BytesIO(binary_data))

        # Prepare BMP data only once
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Standard BMP header is 14 bytes
        output.close()
    except Exception as e:
        print(f"Error processing image data before clipboard attempt: {e}")
        return False # Cannot proceed if image data is invalid

    for attempt in range(retries):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            # print(f"Debug: Image set to clipboard successfully on attempt {attempt+1}") # Optional debug
            return True # Success
        except pywintypes.error as e:
            if e.winerror == 5 or e.winerror == 1418:
                # print(f"Clipboard access denied/error setting image. Retrying... (Attempt {attempt+1}/{retries})") # Optional debug
                try:
                    win32clipboard.CloseClipboard()
                except pywintypes.error:
                    pass
                time.sleep(delay)
            else:
                print(f"Unexpected pywintypes error setting clipboard image: {e}")
                try:
                    win32clipboard.CloseClipboard()
                except pywintypes.error:
                    pass
                # Decide whether to raise or just report failure
                # raise e
                return False # Indicate failure
        except Exception as e:
            print(f"Unexpected error setting clipboard image: {e}")
            try:
                win32clipboard.CloseClipboard()
            except pywintypes.error:
                pass
            # Decide whether to raise or just report failure
            # raise e
            return False # Indicate failure

    print(f"Failed to set image to clipboard after {retries} attempts.")
    return False

def _get_clipboard_content(retries: int = 3, delay: float = 0.2) -> str | None:
    """Internal helper to read text from the clipboard with retry logic."""
    last_error = None
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            # Use CF_UNICODETEXT for expected text data
            response = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return response  # Success
        except (pywintypes.error, TypeError) as e:
            last_error = e
            try:
                # Ensure clipboard is closed even on error
                win32clipboard.CloseClipboard()
            except pywintypes.error:
                pass  # Ignore if it wasn't open
            time.sleep(delay)
        except Exception as e:
            print(f"Unexpected critical error when reading clipboard: {e}")
            try:
                win32clipboard.CloseClipboard()
            except pywintypes.error:
                pass
            raise # Re-raise other critical exceptions
    # print(f"Failed to get clipboard content after retries. Last error: {last_error}") # Optional debug
    return None # Return None on failure

def talkto(llm: str, prompt: str, imagedata: list[str] | None = None, debug: bool = False, tabswitch: bool = True) -> str:
    """
    Interacts with a specified Large Language Model (LLM) via browser automation.

    Args:
        llm: The name of the LLM ('deepseek' or 'gemini').
        prompt: The text prompt to send.
        imagedata: Optional list of base64 encoded image strings.
        debug: Enable debugging output.
        tabswitch: Switch focus back after closing the LLM tab.

    Returns:
        The LLM's response as a string, or an empty string if retrieval fails.
    """

    llm = llm.lower()
    imgpath = ''

    if llm == 'nanobanana':
        imgpath = 'aistudio'
    elif llm not in ['deepseek', 'gemini','aistudio', 'nanobanana']:
        raise ValueError(f"Unsupported LLM: {llm}. Choose 'deepseek', 'gemini', 'aistudio', or 'nanobanana'.")
    else:
        imgpath = llm

    set_image_path(imgpath, debug=debug) # Ensure images for optimiseWait are ready

    urls = {
        'deepseek': 'https://chat.deepseek.com/',
        'gemini': 'https://gemini.google.com/app',
        'aistudio': 'https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-preview',
        'nanobanana': 'https://aistudio.google.com/prompts/new_chat?model=gemini-2.5-flash-image-preview'
    }

    try:
        webbrowser.open_new_tab(urls[llm])
        sleep(0.5) # Allow browser tab to open and load initial elements

        optimiseWait(['message','ormessage','type3','message2','typeytype','tyre','typenew', 'typeplz'], clicks=2, interrupter=['chrome','aistudio','aistudio2'], interrupterclicks=[1,0,0])

        if imagedata:
            for i, img_b64 in enumerate(imagedata):
                if debug: print(f"Processing image {i+1}/{len(imagedata)}")
                if set_clipboard_image(img_b64):
                    pyautogui.hotkey('ctrl', 'v')
                    if debug: print(f"Pasted image {i+1}. Waiting for upload...")
                    sleep(7)
                else:
                    print(f"Warning: Failed to set image {i+1} to clipboard. Skipping paste.")
            sleep(0.5)

        if debug: print("Setting prompt to clipboard...")
        set_clipboard(prompt)
        if debug: print("Pasting prompt...")
        pyautogui.hotkey('ctrl', 'v')
        
        sleep(0.5)

        pyautogui.press('enter')
        pyautogui.hotkey('ctrl', 'enter')

        if llm == 'gemini':
            optimiseWait('send')

        # Set a placeholder value to detect when the clipboard has been updated
        set_clipboard('talktollm: awaiting response')
        # Get the sequence number *after* setting the placeholder
        initial_sequence_number = win32clipboard.GetClipboardSequenceNumber()

        if debug: print("Waiting for LLM response generation (using 'copy' as proxy)...")
        # optimisewait clicks the copy button for us
        result = optimiseWait(['copy', 'orcopy','copy2','copy3','cop4','copyorsmthn','copyimage'], clicks=0)
        if debug:
            print(result)

        sleep(1)

        result = optimiseWait(['copy', 'orcopy','copy2','copy3','cop4','copyorsmthn','copyimage'])
        if debug:
            print(result)

        if debug: print("Copy clicked")

        # --- REVISED LOGIC: Wait for clipboard content to change using sequence number ---
        start_time = time.time()
        timeout = 20  # seconds
        poll_interval = 0.2  # seconds

        if debug:
            print(f"Waiting for clipboard to update (timeout: {timeout}s)... Initial sequence: {initial_sequence_number}")

        response = ""
        while time.time() - start_time < timeout:
            current_sequence_number = win32clipboard.GetClipboardSequenceNumber()
            # If the sequence number is different, the clipboard has changed.
            if current_sequence_number != initial_sequence_number:
                if debug:
                    print(f"Clipboard changed! Sequence number updated from {initial_sequence_number} to {current_sequence_number}.")

                # Now that we know it changed, try to get the content as text.
                clipboard_content = _get_clipboard_content()

                if clipboard_content is not None:
                    # Successfully retrieved text content
                    response = clipboard_content
                    if debug:
                        print(f"Clipboard updated with TEXT successfully after {time.time() - start_time:.2f} seconds.")
                else:
                    # Clipboard changed, but it's not text (it's an image or other format).
                    # We can't return the image data, so we return a success message.
                    response = "[Image copied to clipboard]"
                    if debug:
                        print(f"Clipboard updated with non-text data (likely IMAGE) after {time.time() - start_time:.2f} seconds.")
                
                break # Exit the loop on successful detection

            time.sleep(poll_interval) # Wait before the next check
        else: # This block runs if the while loop finishes without a 'break' (i.e., times out)
            print(f"Timeout: Clipboard did not update within {timeout} seconds.")
            pyautogui.hotkey('ctrl', 'w')
            sleep(0.5)
            if tabswitch:
                pyautogui.hotkey('alt', 'tab')
            return ""
        # --- END OF REVISED LOGIC ---

        if debug: print("Closing tab...")
        pyautogui.hotkey('ctrl', 'w')
        sleep(0.5)

        if tabswitch:
            if debug: print("Switching tab...")
            pyautogui.hotkey('alt', 'tab')

        return response

    except Exception as e:
        print(f"An error occurred during the talkto process: {e}")
        try:
            win32clipboard.CloseClipboard()
        except pywintypes.error:
            pass
        return ""
    
# Example usage (assuming this file is run directly or imported)
if __name__ == "__main__":

    """print("Running talkto example...")
    # Ensure optimisewait images for 'gemini' are available
    # in talktollm/images/gemini/message.png, run.png, copy.png
    response_text = talkto('nanobanana', 'Create a comic in a display of an old school comic book shop about a superman called snooker table man. Show only the cover.', debug=True)
    print("\n--- LLM Response (Text) ---")
    print(response_text)
    print("---------------------------\n")"""

        
    dummy_img = Image.new('RGB', (60, 30), color = 'red')
    buffered = io.BytesIO()
    dummy_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    img_data_uri = f"data:image/png;base64,{img_str}"

    print("Running talkto example with image...")
    response_img = talkto('aistudio', 'Describe this image.', imagedata=[img_data_uri], debug=True)
    print("\n--- LLM Response (Image) ---")
    print(response_img)
    print("----------------------------\n") 
