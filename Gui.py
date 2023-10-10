from nicegui import ui

from Data import *
from config import CONFIG
from log import logger

COLUMNS = [
    {"name": "id", "label": "ID", "field": "id", "required": True, "sortable": True, "align": "left"},
    {"name": "title", "label": "Title", "field": "title", "required": True, "sortable": True, "align": "left"},
    {"name": "artist", "label": "Artist", "field": "artist", "required": True, "sortable": True, "align": "left"},
    {"name": "genres", "label": "Genres", "field": "genres", "required": True, "sortable": True, "align": "left"},
    {"name": "length", "label": "Length", "field": "length", "required": True, "sortable": True, "align": "left"},
    {"name": "path", "label": "Path", "field": "path", "required": True, "sortable": True, "align": "left"}]


class App:
    def __init__(self):
        self.backend = Backend()

        with ui.splitter(limits=(50, 50)).classes("w-full no-wrap") as splitter:
            with splitter.before:
                # Import/Update menu
                with ui.row() as row:
                    row.tailwind.margin("mb-5").margin("ms-5")
                    ui.icon(name="import_export", size="25px")
                    ui.label(text="Import & Update Menu").tailwind.font_weight("bold")

                # Import/Update components
                with ui.column() as column:
                    column.tailwind.margin("ms-5").margin("me-5")

                    with ui.row():
                        self.select_dir = ui.select(options=[], label="Select directory")
                        self.select_dir.tailwind.width("52")
                        self.refresh_dirs()
                        ui.button(text="Load", icon="download",
                                  on_click=lambda: self.refresh_tracks())
                        ui.button(text="Import", icon="library_add",
                                  on_click=lambda: self.import_tracks(self.select_dir.value))

                    with ui.row():
                        ui.button(text="Discover directories", icon="search",
                                  on_click=lambda: self.refresh_dirs())
                        ui.button(text="Reload metadata", icon="refresh",
                                  on_click=lambda: self.reload_tracks(self.select_dir.value))

                    self.import_progress = ui.linear_progress(value=0)

            with splitter.after:
                # Genre menu
                with ui.row() as row:
                    row.tailwind.margin("mb-5").margin("ms-5")
                    ui.icon(name="music_video", size="25px")
                    ui.label(text="Genre Menu").tailwind.font_weight("bold")

                # Genre components
                with ui.row() as row:
                    row.tailwind.margin("ms-5").margin("me-5")

                    self.select_genre = ui.select(options=[], label="Available Genres")
                    self.select_genre.tailwind.width("52")
                    self.refresh_genres()
                    self.input_genre = ui.input(label="Add new genre")
                    self.input_genre.tailwind.width("52")
                    ui.button(text="Add", icon="add",
                              on_click=lambda: self.add_genre(self.input_genre.value))
                    ui.button(text="Remove", icon="remove",
                              on_click=lambda: self.remove_genre(self.select_genre.value))

        # Table
        self.table = ui.table(columns=COLUMNS, rows=[], title="Tracks", pagination=50)
        self.table.classes("w-full no-wrap")
        self.refresh_tracks()

    def run(self):
        logger.info("GUI ready. Starting web-app...")
        ui.dark_mode(True)
        ui.run(title="Music Library")
        # TODO: Run on port loaded in config

    def show_info(self, message):
        ui.notify(message, type="info", close_button="OK")

    def refresh_dirs(self):
        self.select_dir.options = self.backend.get_dirs()
        if self.select_dir.options:
            self.select_dir.value = self.select_dir.options[0]

    def refresh_genres(self):
        self.select_genre.options = self.backend.get_genres()
        if self.select_genre.options:
            self.select_genre.value = self.select_genre.options[0]
            self.select_genre.update()

    def add_genre(self, name):
        self.backend.add_genre(name)
        self.refresh_genres()
        self.input_genre.value = None

    def remove_genre(self, name):
        self.backend.remove_genre(name)
        self.refresh_genres()

    def refresh_tracks(self):
        self.table.rows.clear()
        self.table.rows.extend(self.backend.get_tracks(self.select_dir.value))
        self.table.update()

    def import_tracks(self, path):
        self.backend.import_tracks(path, self.import_progress)
        self.refresh_tracks()
        self.show_info("Tracks imported")

    def reload_tracks(self, path):
        self.backend.reload_tracks(path, self.import_progress)
        self.refresh_tracks()
        self.show_info("Metadata reloaded")
