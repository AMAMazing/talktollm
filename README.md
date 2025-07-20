# talktollm

[![PyPI version](https://badge.fury.io/py/talktollm.svg)](https://badge.fury.io/py/talktollm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python utility for interacting with large language models (LLMs) through browser automation. It leverages image recognition to automate interactions with LLM web interfaces, enabling seamless conversations and task execution.

## Features

-   **Simple Interface:** Provides a single, intuitive function for interacting with LLMs.
-   **Automated Image Recognition:** Employs image recognition (`optimisewait`) to identify and interact with elements on the LLM interface.
-   **Multi-LLM Support:** Supports DeepSeek, Gemini, and Google AI Studio.
-   **Automated Conversations:** Facilitates automated conversations and task execution by simulating user interactions.
-   **Image Support:** Allows sending one or more images (as base64 data URIs) to the LLM.
-   **Robust Clipboard Handling:** Includes retry mechanisms for setting and getting clipboard data, handling common access errors and timing issues.
-   **Self-Healing Image Cache:** Creates a clean, temporary image cache for each run, preventing issues from stale or corrupted recognition assets.
-   **Easy to use:** Designed for simple setup and usage.

## Core Functionality

The core function is `talkto(llm, prompt, imagedata=None, debug=False, tabswitch=True)`.

**Arguments:**

-   `llm` (str): The LLM name ('deepseek', 'gemini', or 'aistudio').
-   `prompt` (str): The text prompt to send.
-   `imagedata` (list[str] | None): Optional list of base64 encoded image data URIs (e.g., "data:image/png;base64,...").
-   `debug` (bool): Enable detailed console output. Defaults to `False`.
-   `tabswitch` (bool): Switch focus back to the previous window after closing the LLM tab. Defaults to `True`.

**Steps:**

1.  Validates the LLM name.
2.  Ensures a clean temporary image cache is ready for `optimisewait`.
3.  Opens the LLM's website in a new browser tab.
4.  Waits for and clicks the message input area.
5.  If `imagedata` is provided, it pastes each image into the input area.
6.  Pastes the `prompt` text.
7.  Clicks the 'run' or 'send' button.
8.  Sets a placeholder value on the clipboard.
9.  Waits for the 'copy' button to appear (indicating the response is ready) and clicks it.
10. Polls the clipboard until its content changes from the placeholder value.
11. Closes the browser tab (`Ctrl+W`).
12. Switches focus back if `tabswitch` is `True` (`Alt+Tab`).
13. Returns the retrieved text response, or an empty string if the process times out.

## Helper Functions

**Clipboard Handling:**

-   `set_clipboard(text: str, retries: int = 5, delay: float = 0.2)`: Sets text to the clipboard. Retries on common access errors.
-   `set_clipboard_image(image_data: str, retries: int = 5, delay: float = 0.2)`: Sets a base64 encoded image to the clipboard. Retries on common access errors.
-   `_get_clipboard_content(...)`: Internal helper to read text from the clipboard with retry logic.

**Image Path Management:**

-   `copy_images_to_temp(llm: str, debug: bool = False)`: **Deletes and recreates** the LLM-specific temporary image folder to ensure a clean state. Copies necessary `.png` images from the package's internal `images/` directory to the temporary location.

## Installation

```
pip install talktollm
```

*Note: Requires `optimisewait` for image recognition. Install separately if needed (`pip install optimisewait`).*

## Usage

Here are some examples of how to use `talktollm`.

**Example 1: Simple Text Prompt**

Send a basic text prompt to Gemini.

```python
import talktollm

prompt_text = "Explain quantum entanglement in simple terms."
response = talktollm.talkto('gemini', prompt_text)
print("--- Simple Gemini Response ---")
print(response)
```

**Example 2: Text Prompt with Debugging**

Send a text prompt to AI Studio and enable debugging output.

```python
import talktollm

prompt_text = "What are the main features of Python 3.12?"
response = talktollm.talkto('aistudio', prompt_text, debug=True)
print("--- AI Studio Debug Response ---")
print(response)
```

**Example 3: Preparing Image Data**

Load an image file, encode it in base64, and format it correctly for the `imagedata` argument.

```python
import base64

# Load your image (replace 'path/to/your/image.png' with the actual path)
try:
    with open("path/to/your/image.png", "rb") as image_file:
        # Encode to base64
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # Format as a data URI
        image_data_uri = f"data:image/png;base64,{encoded_string}"
        print("Image prepared successfully!")
except FileNotFoundError:
    print("Error: Image file not found. Please check the path.")
    image_data_uri = None

# This 'image_data_uri' variable holds the string needed for the next example
```

**Example 4: Text and Image Prompt**

Send a text prompt along with a prepared image to DeepSeek. (Assumes `image_data_uri` was successfully created in Example 3).

```python
import talktollm

# Assuming image_data_uri is available from the previous example
if image_data_uri:
    prompt_text = "Describe the main subject of this image."
    response = talktollm.talkto(
        'deepseek',
        prompt_text,
        imagedata=[image_data_uri], # Pass the image data as a list
        debug=True
    )
    print("--- DeepSeek Image Response ---")
    print(response)
else:
    print("Skipping image example because image data is not available.")
```

## Dependencies

-   `pywin32`: For Windows API access (clipboard).
-   `pyautogui`: For GUI automation (keystrokes).
-   `Pillow`: For image processing.
-   `optimisewait` (Recommended): For robust image-based waiting and clicking.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT
