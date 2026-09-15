# Lyriclook

Lyriclook is a small PyQt6 desktop application for searching `.lrc` and `.txt` files in a local music library. Searches are case-insensitive, and an optional artist filter matches artist directory names case-insensitively by substring.

## Run

From this directory:

```bash
python3 main.py
```

Enter a lyric fragment, choose the music folder, and optionally enter an artist. The default music folder is the launching user's `~/Music` directory. Double-click a result to open the matching song with the system default audio player; the audio file must share the lyric file's title and directory. The chosen music folder is saved in `~/.config/lyriclook/settings.json`.

## Test

The search layer uses only the Python standard library and the system `grep` command:

```bash
python3 -m unittest discover -s tests -v
```

Install the GUI dependency with:

```bash
python3 -m pip install -r requirements.txt
```