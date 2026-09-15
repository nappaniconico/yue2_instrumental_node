# YuE2 Instrumental ABC for ComfyUI

English | [日本語](README.ja.md)

ComfyUI custom nodes for editing YuE2-generated ABC scores for instrumental music.

**Move the Vocal melody into fully resting Ins bars, then mute Vocal while preserving chord progressions and existing Ins melodies.** A separate node lets you mute Vocal without transferring its melody.

These nodes process ABC text and require no additional models or Python packages. Audio generation requires a separate ComfyUI setup capable of running YuE2.

## Nodes

Category: `YuE2/ABC`

| Node | What it does | Use it when |
| --- | --- | --- |
| **YuE2 Instrumentalize ABC** | Copies Vocal melody into fully resting Ins bars, then mutes Vocal | You want to retain the main melody in an instrumental arrangement |
| **YuE2 Mute Vocal ABC** | Replaces only Vocal notes with rests of the same duration | You want to remove the Vocal melody |

## Installation

### Install with Git

Run this command from ComfyUI's `custom_nodes` directory:

```bash
git clone https://github.com/nappaniconico/yue2_instrumental_node.git yue2_instrumental
```

Restart ComfyUI. The nodes will be available in node search.

### Install from ZIP

1. Download this repository using **Code → Download ZIP**.
2. Rename the extracted folder to `yue2_instrumental` and place it inside ComfyUI's `custom_nodes` directory.
3. Restart ComfyUI.

Check that the directory structure looks like this:

```text
ComfyUI/
└── custom_nodes/
    └── yue2_instrumental/
        ├── __init__.py
        ├── nodes.py
        ├── abc_mute.py
        └── instrumentalize.py
```

## Usage

Connect either node between ABC generation and audio generation:

```text
YuE2 ABC generation node
        │ ABC string
        ▼
YuE2 Instrumentalize ABC
        │ abc output
        ▼
YuE2 audio generation node
```

1. Add **YuE2 Instrumentalize ABC**.
2. Connect the generated ABC string to its `abc` input. You can also paste ABC text directly into the node.
3. Connect its `abc` output to the audio generation node's ABC input.
4. Connect `moved_bars` or `report` to a compatible display node to inspect the results.

**Feed the original ABC into Instrumentalize.** If you place it after Mute Vocal, the Vocal melody will already have been removed and cannot be transferred.

To remove the Vocal melody, use **YuE2 Mute Vocal ABC** in the same position instead. YuE2 node names and input names vary by extension. These nodes use `STRING` for ABC input and output.

## YuE2 Instrumentalize ABC

### How it works

Each bar is processed using these rules:

1. **Ins contains only rests and Vocal has notes:** Copy the Vocal melody into Ins.
2. **Ins contains any notes:** Preserve the entire Ins bar. The node does not fill individual rests within an otherwise occupied bar.
3. **All Vocal notes:** Replace them with rests of the original duration. Keep chord symbols at their original positions in Vocal.

Supports full-bar and multi-bar rests such as `Z`, `Z2`, and `Z3`, as well as bars made entirely of ordinary rests, such as `z4z4`. Multi-bar rests are expanded only when needed.

### Example

Input:

```abc
M:4/4
L:1/8
K:C
V: Vocal
"C"C4E4|"G"G8|
V: Ins
Z|d8|
```

Output:

```abc
M:4/4
L:1/8
K:C
V: Vocal
"C"z4z4|"G"z8|
V: Ins
=C4=E4|d8|
```

The first bar receives the Vocal melody. The existing `d8` in the second bar is preserved. The chord symbols `"C"` and `"G"` stay in place.

Copied notes include explicit accidentals, including `=` for natural notes, to preserve pitches determined by the original key, accidentals, and ties across barlines. Ties between transferred notes are retained; ties extending into bars that are not transferred are removed.

### Inputs and outputs

Input: `abc` (`STRING`), the original ABC score.

| Output | Type | Description |
| --- | --- | --- |
| `abc` | `STRING` | Converted ABC |
| `muted_notes` | `INT` | Number of Vocal note tokens replaced with rests |
| `moved_bars` | `INT` | Number of bars where Vocal melody was copied into Ins |
| `report` | `STRING` | Summary of transferred bars and bars where existing Ins melody took priority |

### Supported notation

The node targets YuE2's monophonic ABC format and validates both the input and the converted score.

- **Required:** A single tune with explicit `M:` (meter), `L:` (unit note length), and `K:` (key) headers. Voice IDs must be `Vocal` and `Ins`.
- **Bars:** Both voices must have matching bar counts, bar durations, unit note lengths, keys, and inline key-change positions. Each bar must end with a barline.
- **Supported:** Major and minor keys, ordinary notes and rests, fractional durations, ties, multi-bar rests, `[K:...]` key changes, and bars spanning multiple text lines.
- **Unsupported:** Incomplete bars such as pickups, tuplets, decorations, simultaneous note stacks, repeat signs, inline voice switches, `w:` lyrics, chord annotations in Ins, and other notation outside the supported format.

Unsupported notation or duration mismatches produce an error. The node does not automatically fall back to Mute Vocal. Original comments and headers are preserved, but note spelling and whitespace placement may change where melody is transferred.

## YuE2 Mute Vocal ABC

Replaces Vocal notes with rests of the same duration and removes their ties. Notes in Ins and other voices are preserved.

Input:

```abc
V: Vocal
"C"C4E4|"G"G8|
V: Ins
Z|d8|
```

Output:

```abc
V: Vocal
"C"z4z4|"G"z8|
V: Ins
Z|d8|
```

Input: `abc` (`STRING`), the original ABC score.

| Output | Type | Description |
| --- | --- | --- |
| `abc` | `STRING` | Converted ABC |
| `muted_notes` | `INT` | Number of Vocal note tokens replaced with rests |

Preserves durations, chord positions, barlines, headers, comments, and line endings. Supports accidentals, octave markers, fractional durations, and inline voice/key fields. Grace notes `{...}` and simultaneous note stacks such as `[CEG]` in Vocal produce an error.

This node is not a general-purpose ABC validator. Some ABC accepted by Mute Vocal may be rejected by Instrumentalize's stricter bar validation.

## FAQ

### The nodes do not appear in search

Check that the installation includes `custom_nodes/yue2_instrumental/__init__.py`, then restart ComfyUI. If the nodes still do not appear, check the startup log for import errors.

### `muted_notes` is 0

This means no matching notes were found. Check that the voice ID is exactly `Vocal` (case-sensitive) and that the input has not already been muted. Tied notes are counted as individual note tokens.

### `moved_bars` is 0

No bars met both conditions: Vocal contains notes and the corresponding Ins bar contains only rests. Bars with any existing Ins notes are not transfer targets.

### The generated audio still has vocals or uses an unexpected instrument

These nodes edit ABC scores. They do not remove vocals from generated audio or select instruments. Set the audio generator's lyrics and style for instrumental music as well. Mute Vocal leaves lyric fields unchanged; Instrumentalize rejects `w:` lyric fields. Neither node changes external lyrics inputs.

Muting or transferring melody in ABC does not guarantee vocal-free audio or a particular instrument. Comparing the original and converted ABC with the same generation seed can help you assess the effect.

## Development and tests

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

Tests use only the Python standard library and require neither ComfyUI nor a GPU. They cover node registration, muting, multi-bar rests, preservation of existing Ins melody, note onsets/durations/pitches, chord positions, ties, key changes, and rejection of unsupported input.

## References

- [YuE repository](https://github.com/multimodal-art-projection/YuE)
- [Official YuE2 ABC editing guide](https://github.com/multimodal-art-projection/YuE/blob/main/skills/yue2-music/references/abc-editing.md)
