---
name: screen-marker
description: >-
  Use this skill whenever the user enters `/screen-marker`, `/screen show`, `/screen`, or wants to visually mark, circle, highlight, or draw on their screen to request UI or code changes on a website, web app, or desktop application.
---

# Screen Marker & Visual Feedback Skill

This skill provides an interactive screen-drawing overlay that allows the user to freeze their current screen, draw annotations (pens, arrows, bounding boxes, highlighters, and text notes), type instructions, and submit them directly to the AI agent to make the changes in their codebase.

## Workflow

### 1. Launch the Screen Marker Overlay

When the user enters `/screen-marker`, `/screen show`, or `/screen`, execute the screen marker passing `--caller-chat`:

```powershell
python "C:\Users\HP\.gemini\config\skills\screen-marker\scripts\screen_marker.py" --caller-chat "<CURRENT_CONVERSATION_ID>"
```

### 2. Capture and Parse Feedback

The script will launch a fullscreen overlay on the user's desktop where they can:
- **`Tab`** to toggle **Browse Desktop** mode to scroll or navigate, then **`Space`** to freeze.
- **Draw** freehand marks with the Pen ✏️
- **Highlight** regions with the translucent Highlighter 🖍️
- **Box** components or elements with the Bounding Box tool 🔲
- **Point** to elements with the Arrow tool ➡️
- **Add text notes** directly onto the screen 🔤
- Type their prompt instruction in the floating toolbar input box
- Click **Send to AI (Enter)**

When submitted, the script outputs a JSON block delimited by:
`---SCREEN_MARKER_RESULT_START---` and `---SCREEN_MARKER_RESULT_END---`.

The JSON payload contains:
- `instruction`: The text prompt typed by the user.
- `annotated_image`: Path to the image containing the user's drawn markers and arrows.
- `clean_image`: Path to the original unblemished screenshot.
- `shapes`: Array of drawn shapes with bounding coordinates.
- `metadata_file`: Path to the saved JSON metadata.

### 3. Read and Inspect the Annotated Capture

Use the `read_file` tool on `annotated_image` to inspect the visual markings:
- Notice where the circles, boxes, and arrows point.
- Note any text notes placed directly on screen.
- Correlate the visual position with the active website or application UI structure.

### 4. Locate and Modify the Codebase

1. Search the workspace codebase for the text, class names, IDs, components, or layout structures shown in the marked area.
2. Cross-reference the user's instructions (e.g., color tweaks, margins, alignment, button click handlers, new components, text changes).
3. Use `edit_file` to apply the exact changes to the HTML, CSS, React, Vue, Python, or styling files.

### 5. Verify and Report

1. Confirm that the modified code matches the user's drawn intentions.
2. Provide a clear summary with file links explaining the modifications made.
