# Lyriclook

Lyriclook is a small PyQt6 desktop application for searching `.lrc` and `.txt` files in a local music library.<br><br>
Searches are case-insensitive, and an optional artist filter matches artist directory names case-insensitively by substring.<br><br>
Enter a lyric fragment, choose the music folder, and optionally enter an artist. The default music folder is the launching user's `~/Music` directory.<br><br>
The results are grouped by song, and songs are separated by a newline.<br><br>
Double-click a result to open the matching song with the system default audio player; the audio file must share the lyric file's title and directory.<br><br>
The chosen music folder is saved in `~/.config/lyriclook/settings.json`.

## Run

From this directory:

```bash
python3 main.py
```

## Notes
I was sick of having to type the whole ```grep -r "lyric" /properly/capitalised/path/to/music``` so I made a wrapper that takes care of that. I love making my life easier.
