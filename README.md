# Screen Marker & Visual Feedback Skill for Antigravity

An interactive live screen-annotation and visual feedback tool designed for Antigravity AI agents.

Freeze your active display, mark up bugs, alignment issues, or desired design changes with highlighters, bounding boxes, arrows, or freehand drawing, type your instructions, and let your AI agent inspect the visual annotations and automatically implement the changes in your codebase.

---

## Features

- ✏️ **Freehand Pen**: Draw, circle, and annotate any part of the screen.
- 🖍️ **Neon Highlighter**: Translucent highlighter for text blocks and containers.
- 🔲 **Bounding Box**: Frame components, buttons, navigation bars, or modals.
- ➡️ **Directional Arrow**: Point directly to elements needing changes.
- 🔤 **Text Note**: Drop custom text badges anywhere on screen.
- 🌐 **Browse Desktop Mode (`Tab` / `F2`)**: Collapses into a floating pill so you can freely scroll, navigate, or switch tabs, then press `Space` to freeze and mark.
- 🗗 **Resizable Window Mode**: Switch between Fullscreen and a resizable, draggable floating window.
- 🔄 **Live Recapture**: Instantly refresh the screenshot without restarting the tool.
- 🎯 **Targeted Chat Routing**: Feedback is returned strictly to the chat session where the command was issued.
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

Whenever you want to modify a website or desktop app, simply type in your chat:
> **`/screen`** or **`/screen show`** or **`/screen-marker`**

The agent will execute:
```bash
python scripts/screen_marker.py --caller-chat "<CURRENT_CONVERSATION_ID>"
```

### What Happens:
1. The overlay opens on your screen.
2. You can navigate/scroll (`Tab`), freeze (`Space`), and mark what to change.
3. You type your instruction and press `Enter`.
4. The marked screenshot and prompt are delivered **directly into that chat session**.
5. The AI agent inspects your markings and automatically modifies the code in your workspace.

---

## Standalone Usage

Double-click `scripts/launch_marker.bat` or run:
```bash
python scripts/screen_marker.py
```
Outputs are saved by default to:
`~/.gemini/antigravity/screen_feedback/`
