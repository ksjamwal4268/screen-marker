# Screen Marker & Visual Feedback Skill for Antigravity

An interactive live screen-annotation and visual feedback skill designed for Antigravity AI agents.

Freeze your active display, mark up bugs, alignment issues, or desired design changes with highlighters, bounding boxes, arrows, or freehand drawing, type your instructions, and let your AI agent inspect the visual annotations and automatically implement the changes in your codebase.

---

## Features

- ✏️ **Freehand Pen**: Draw, circle, and annotate any part of the screen.
- 🖍️ **Neon Highlighter**: Translucent highlighter for text blocks and containers.
- 🔲 **Bounding Box**: Frame components, buttons, navigation bars, or modals.
- ➡️ **Directional Arrow**: Point directly to elements needing changes.
- 🔤 **Text Note**: Drop custom text badges anywhere on screen.
- 🎨 **Color Palette**: Instant switching between Red, Yellow, Blue, Green, and Purple.
- ↩️ **Undo / Clear**: `Ctrl+Z` support and canvas clearing.
- 💬 **Instruction Bar**: Enter prompts like *"Make this button navy blue and align it to the right"*.
- 🚀 **Send to AI (`Enter`)**: Saves the marked screenshot, original clean screenshot, and coordinates JSON metadata.

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Required packages:
  ```bash
  pip install PyQt5 mss Pillow
  ```

---

## Usage with Antigravity Agent

Whenever you want to modify a website or desktop app, ask your agent:
> *"Let me mark on my screen what I want to change on this page."*
> or
> *"Open the screen marker."*

The agent will execute:
```bash
python scripts/screen_marker.py
```
And upon submitting, the agent will:
1. Read the marked screenshot and the exact shape coordinates.
2. Read your instruction prompt.
3. Locate the corresponding code in your workspace.
4. Apply the modifications and verify the result.

---

## Standalone Usage

Double-click `scripts/launch_marker.bat` or run:
```bash
python scripts/screen_marker.py
```
Outputs are saved by default to:
`~/.gemini/antigravity/screen_feedback/`
