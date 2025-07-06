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
    """Copies the necessary image files to a temporary directory."""
    temp_dir = tempfile.gettempdir()
    image_path = os.path.join(temp_dir, 'talktollm_images', llm)
    os.makedirs(image_path, exist_ok=True)
    if debug:
        print(f"Temporary image directory: {image_path}")

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

# --- MODIFIED talkto FUNCTION ---
def talkto(llm: str, prompt: str, imagedata: list[str] | None = None, debug: bool = False, tabswitch: bool = True, read_retries: int = 5, read_delay: float = 0.3) -> str:
    """
    Interacts with a specified Large Language Model (LLM) via browser automation.

    Args:
        llm: The name of the LLM ('deepseek' or 'gemini').
        prompt: The text prompt to send.
        imagedata: Optional list of base64 encoded image strings.
        debug: Enable debugging output.
        tabswitch: Switch focus back after closing the LLM tab.
        read_retries: Number of attempts to read the clipboard.
        read_delay: Delay (seconds) between read retries.

    Returns:
        The LLM's response as a string, or an empty string if retrieval fails.
    """
    llm = llm.lower()
    if llm not in ['deepseek', 'gemini']:
        raise ValueError(f"Unsupported LLM: {llm}. Choose 'deepseek' or 'gemini'.")

    set_image_path(llm, debug=debug) # Ensure images for optimiseWait are ready

    urls = {
        'deepseek': 'https://chat.deepseek.com/',
        'gemini': 'https://aistudio.google.com/prompts/new_chat' # Or specific Gemini chat URL if available
    }

    try:
        webbrowser.open_new_tab(urls[llm])
        # Add a small delay to allow the browser tab to open and potentially load initial elements
        sleep(2) # Adjust as needed

        optimiseWait(['message','ormessage','type3'], clicks=2) # Assumes 'message' image corresponds to the input field

        # If there are images, paste each one
        if imagedata:
            for i, img_b64 in enumerate(imagedata):
                if debug: print(f"Processing image {i+1}/{len(imagedata)}")
                if set_clipboard_image(img_b64):
                    pyautogui.hotkey('ctrl', 'v')
                    if debug: print(f"Pasted image {i+1}. Waiting for upload...")
                    # Wait *after* pasting for potential upload indication or just a fixed time
                    sleep(7) # Adjust based on typical upload time / LLM interface behavior
                else:
                    print(f"Warning: Failed to set image {i+1} to clipboard. Skipping paste.")
            # Add a small delay after the last image paste before pasting prompt
            sleep(0.5)

        if debug: print("Setting prompt to clipboard...")
        set_clipboard(prompt) # Uses built-in retries
        if debug: print("Pasting prompt...")
        pyautogui.hotkey('ctrl', 'v')

        sleep(1) # Allow paste to register

        if debug: print("Clicking 'run'...")
        optimiseWait('run') # Assumes 'run' image corresponds to the submit/send button

        # Wait for the response to generate - this might need adjustment or a different optimisewait target
        if debug: print("Waiting for LLM response generation (using 'copy' as proxy)...")
        optimiseWait(['copy', 'orcopy','copy2']) # Assumes 'copy' image appears *after* response is generated and ready

        # Click the copy button (optimiseWait already did this)

        # Add a small explicit delay AFTER clicking copy, before closing tab
        sleep(0.5) # Give the browser time to execute the copy command
        if debug: print("Closing tab...")
        pyautogui.hotkey('ctrl', 'w')
        sleep(0.5) # Allow tab to close fully

        if tabswitch:
            if debug: print("Switching tab...")
            pyautogui.hotkey('alt', 'tab')

        # --- Get LLM's response with retry logic ---
        if debug: print("Attempting to read clipboard...")
        response = None
        last_error = None
        for attempt in range(read_retries):
            try:
                win32clipboard.OpenClipboard()
                # Crucially use CF_UNICODETEXT for expected text data
                response = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                if debug:
                    print(f"Successfully retrieved clipboard data on attempt {attempt+1}")
                break  # Success, exit the loop
            except pywintypes.error as e:
                last_error = e
                if e.winerror == 5:  # Access is denied
                    if debug:
                        print(f"Clipboard access denied on read. Retrying in {read_delay}s... (Attempt {attempt+1}/{read_retries})")
                # Handle case where clipboard might not be open yet after error
                elif e.winerror == 1418: # ERROR_CLIPBOARD_NOT_OPEN
                     if debug:
                        print(f"Clipboard not open error on read. Retrying in {read_delay}s... (Attempt {attempt+1}/{read_retries})")
                else:
                    print(f"Unexpected pywintypes error when reading clipboard: {e}")
                    try:
                        win32clipboard.CloseClipboard() # Ensure closed even on unexpected error
                    except pywintypes.error:
                        pass # Ignore error if closing failed
                    # Depending on severity, you might want to break or raise here
                    # For now, we'll let it retry
                try:
                    # Ensure clipboard is closed if OpenClipboard succeeded but GetClipboardData failed with pywintypes error
                    win32clipboard.CloseClipboard()
                except pywintypes.error:
                    pass # Ignore if it wasn't open
                time.sleep(read_delay) # Wait before retrying

            except TypeError as e:
                 last_error = e
                 # This often means the clipboard is empty or contains non-text data
                 if debug:
                     print(f"Clipboard empty or contains non-text data on attempt {attempt+1}. Retrying in {read_delay}s...")
                 try:
                     win32clipboard.CloseClipboard()
                 except pywintypes.error:
                     pass # Ignore error if closing failed because it wasn't open
                 time.sleep(read_delay) # Wait and retry
            except Exception as e:
                last_error = e
                print(f"Unexpected error when reading clipboard: {e}")
                try:
                    win32clipboard.CloseClipboard() # Ensure closed
                except pywintypes.error:
                    pass
                raise # Re-raise other critical exceptions immediately
        else: # This block executes if the loop completes without break
            print(f"Failed to get clipboard data after {read_retries} attempts. Last error: {last_error}")
            return "" # Return empty string on failure

        if response is None:
             print("Warning: Failed to retrieve response from clipboard (response is None).")
             return ""

        return response

    except Exception as e:
        print(f"An error occurred during the talkto process: {e}")
        # Attempt to close clipboard just in case it was left open by an error
        try:
            win32clipboard.CloseClipboard()
        except pywintypes.error:
            pass
        # Optionally re-raise the exception if you want the caller to handle it
        # raise e
        return "" # Return empty string or handle error as appropriate


# Example usage (assuming this file is run directly or imported)
if __name__ == "__main__":
    print("Running talkto example...")
    # Ensure optimisewait images for 'gemini' are available
    # in talktollm/images/gemini/message.png, run.png, copy.png
    response_text = talkto('deepseek', 'Explain the difference between a list and a tuple in Python.', debug=True)
    print("\n--- LLM Response (Text) ---")
    print(response_text)
    print("---------------------------\n")

        
    dummy_img = Image.new('RGB', (60, 30), color = 'red')
    buffered = io.BytesIO()
    dummy_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    img_data_uri = f"data:image/png;base64,{img_str}"

    print("Running talkto example with image...")
    response_img = talkto('deepseek', 'Describe this image.', imagedata=[img_data_uri], debug=True)
    print("\n--- LLM Response (Image) ---")
    print(response_img)
    print("----------------------------\n")