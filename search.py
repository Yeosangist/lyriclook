"""Search local lyric files independently of the GUI toolkit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess


SUPPORTED_SUFFIXES = {".lrc", ".txt"}
LYRIC_SUFFIXES = {".lrc", ".txt"}
AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".wma"}


@dataclass(frozen=True)
class SearchResult:
    """One matching line in a lyric file."""

    path: Path
    line_number: int
    line: str


class SearchError(RuntimeError):
    """Raised when a lyric search cannot be completed."""


def find_song_path(lyric_path: Path | str) -> Path | None:
    """Find the non-lyric file sharing a lyric file's title and directory."""

    lyric_path = Path(lyric_path)
    try:
        candidates = sorted(lyric_path.parent.iterdir())
    except OSError:
        return None
    for candidate in candidates:
        if candidate.is_file() and candidate.stem == lyric_path.stem and candidate.suffix.casefold() in AUDIO_SUFFIXES:
            return candidate
    return None


def find_artist_directories(music_dir: Path | str, artist: str) -> list[Path]:
    """Return directories whose names contain ``artist``, ignoring case."""

    root = _validate_music_dir(music_dir)
    artist = artist.strip()
    if not artist:
        return [root]

    folded_artist = artist.casefold()
    matches: list[Path] = []
    for directory in _walk_directories(root):
        if folded_artist in directory.name.casefold():
            matches.append(directory)
    return matches


def search_lyrics(
    music_dir: Path | str,
    lyrics: str,
    artist: str | None = None,
) -> list[SearchResult]:
    """Search supported lyric files recursively using case-insensitive grep."""

    root = _validate_music_dir(music_dir)
    lyrics = lyrics.strip()
    if not lyrics:
        raise ValueError("Lyrics search text cannot be empty")

    roots = [root]
    if artist and artist.strip():
        roots = find_artist_directories(root, artist)
        if not roots:
            return []

    command = [
        "grep",
        "-RniH",
        "--null",
        "--binary-files=without-match",
        "--include=*.lrc",
        "--include=*.txt",
        "--",
        lyrics,
        *(str(path) for path in roots),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise SearchError("grep is not installed or could not be found") from error
    except OSError as error:
        raise SearchError(f"Unable to start search: {error}") from error

    if completed.returncode not in (0, 1):
        detail = completed.stderr.strip() or "grep failed"
        raise SearchError(detail)

    return _parse_grep_output(completed.stdout)


def _validate_music_dir(music_dir: Path | str) -> Path:
    root = Path(music_dir).expanduser()
    if not root.exists():
        raise ValueError(f"Music directory does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Music path is not a directory: {root}")
    if not os.access(root, os.R_OK):
        raise ValueError(f"Music directory is not readable: {root}")
    return root.resolve()


def _walk_directories(root: Path):
    for current, directory_names, _ in os.walk(root):
        directory_names[:] = [name for name in directory_names if not name.startswith(".")]
        yield Path(current)


def _parse_grep_output(output: str) -> list[SearchResult]:
    results: list[SearchResult] = []
    for raw_line in output.splitlines():
        try:
            path_text, match_text = raw_line.split("\x00", 1)
            line_number_text, line = match_text.split(":", 1)
            results.append(
                SearchResult(
                    path=Path(path_text),
                    line_number=int(line_number_text),
                    line=line,
                )
            )
        except (ValueError, IndexError):
            # Ignore malformed output rather than crashing the whole result view.
            continue
    return results