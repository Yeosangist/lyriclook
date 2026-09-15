"""PyQt6 presentation layer for lyric searches."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QWidget,
)

from config import load_settings, save_settings
from search import SearchError, SearchResult, find_artist_directories, find_song_path, search_lyrics


class SearchWorker(QThread):
    completed = pyqtSignal(list, bool, object)

    def __init__(self, music_dir: str, lyrics: str, artist: str) -> None:
        super().__init__()
        self.music_dir = music_dir
        self.lyrics = lyrics
        self.artist = artist

    def run(self) -> None:
        try:
            artist_found = bool(find_artist_directories(self.music_dir, self.artist)) if self.artist else True
            results = search_lyrics(self.music_dir, self.lyrics, self.artist or None)
            error = None
        except (SearchError, ValueError) as exception:
            artist_found = True
            results = []
            error = str(exception)
        self.completed.emit(results, artist_found, error)


class LyricsSearchApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lyriclook")
        self.setMinimumSize(1080, 720)
        self.results: list[SearchResult] = []
        self._displayed_results: list[SearchResult | None] = []
        self._search_worker: SearchWorker | None = None

        settings = load_settings()
        self.lyrics_entry = QLineEdit()
        self.artist_entry = QLineEdit()
        self.music_dir_entry = QLineEdit(settings.get("music_dir", str(Path.home() / "Music")))
        self.search_button = QPushButton("Search")
        self.result_list = QListWidget()
        self.status_label = QLabel("Enter lyrics to search your music library.")
        self._build_widgets()

    def _build_widgets(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(5, 1)

        layout.addWidget(QLabel("Lyrics:"), 0, 0)
        layout.addWidget(self.lyrics_entry, 0, 1, 1, 2)
        self.lyrics_entry.returnPressed.connect(self.start_search)
        self.lyrics_entry.setFocus()

        layout.addWidget(QLabel("Artist:"), 1, 0)
        layout.addWidget(self.artist_entry, 1, 1, 1, 2)

        layout.addWidget(QLabel("Music folder:"), 2, 0)
        layout.addWidget(self.music_dir_entry, 2, 1)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.choose_directory)
        layout.addWidget(browse_button, 2, 2)

        self.search_button.clicked.connect(self.start_search)
        layout.addWidget(self.search_button, 3, 1)

        layout.addWidget(QLabel("Results:"), 4, 0, 1, 3)
        self.result_list.itemDoubleClicked.connect(self.open_selected_result)
        layout.addWidget(self.result_list, 5, 0, 1, 3)
        layout.addWidget(self.status_label, 6, 0, 1, 3)

    def choose_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Choose music folder", self.music_dir_entry.text())
        if selected:
            self.music_dir_entry.setText(selected)

    def start_search(self) -> None:
        lyrics = self.lyrics_entry.text().strip()
        music_dir = self.music_dir_entry.text().strip()
        if not lyrics:
            QMessageBox.warning(self, "Search", "Enter some lyrics to search for.")
            return
        if not music_dir:
            QMessageBox.warning(self, "Search", "Choose a music folder first.")
            return

        self.search_button.setEnabled(False)
        self.status_label.setText("Searching...")
        self.result_list.clear()
        self._search_worker = SearchWorker(music_dir, lyrics, self.artist_entry.text().strip())
        self._search_worker.completed.connect(self._show_results)
        self._search_worker.finished.connect(self._search_finished)
        self._search_worker.start()

    def _search_finished(self) -> None:
        if self._search_worker is not None:
            self._search_worker.deleteLater()
            self._search_worker = None

    def _show_results(self, results: list[SearchResult], artist_found: bool, error: str | None) -> None:
        self.search_button.setEnabled(True)
        self.results = results
        self._displayed_results = []
        self.result_list.clear()
        if error:
            self.status_label.setText(error)
            return
        music_root = Path(self.music_dir_entry.text()).expanduser().resolve()
        previous_path: Path | None = None
        for result in results:
            same_song = previous_path is not None and (
                result.path.parent == previous_path.parent and result.path.stem == previous_path.stem
            )
            if previous_path is not None and not same_song:
                separator = QListWidgetItem("")
                separator.setFlags(separator.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.result_list.addItem(separator)
                self._displayed_results.append(None)
            try:
                display_path = result.path.relative_to(music_root)
            except ValueError:
                display_path = result.path
            self.result_list.addItem(f"{display_path} ({result.line_number}): {result.line}")
            self._displayed_results.append(result)
            previous_path = result.path
        if not artist_found:
            self.status_label.setText("No matching artist directory found.")
        else:
            self.status_label.setText(f"Found {len(results)} matching line(s). Double-click a result to open it.")
        save_settings({"music_dir": self.music_dir_entry.text()})

    def open_selected_result(self, item: QListWidgetItem) -> None:
        result = self._displayed_results[self.result_list.row(item)]
        if result is None:
            return
        song_path = find_song_path(result.path)
        if song_path is None:
            QMessageBox.critical(self, "Play song", f"Could not find a song matching {result.path.name}")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(song_path))):
            QMessageBox.critical(self, "Play song", f"Could not open {song_path} with the system default player")