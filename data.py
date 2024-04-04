import os
import eyed3
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

from config import CONFIG
from log import logger

Base = declarative_base()


def extract_metadata(file):
    audio = eyed3.load(file)

    title = audio.tag.title
    artist = audio.tag.artist
    length = audio.info.time_secs

    # Default title & artist
    if not title and not artist:
        name = os.path.basename(file)
        if name.count("-") == 0:
            title = name.split(".")[0].strip()
        if name.count("-") == 1:
            title = name.split("-")[1].split(".")[0].strip()
            artist = name.split("-")[0].strip()

    # Default length
    if not length:
        length = 0

    return {"title": title,
            "artist": artist,
            "length": length}


class Tracks(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist = Column(String)
    genres = Column(String)  # list of genre-ids
    length = Column(Integer)  # in seconds
    path = Column(String)

    def __repr__(self):
        return f"[TRACK] {self.id} - {self.artist} - {self.title}"

    def __getattr__(self, item):
        # Unpack multiple values
        if ";" in item:
            item = item.split(";")

        return super().__getattr__(item)

    def __setattr__(self, key, value):
        # Handle only for 'genres' attribute
        if key in ("genres",):
            # Pack multiple values
            if hasattr(value, "__iter__"):
                cache = ""
                for v in value:
                    cache += str(v) + ";"
                value = cache[:-1]

        return super().__setattr__(key, value)


class Genres(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f"[GENRE] {self.id} - {self.name}"


class Backend:
    def __init__(self):
        engine = create_engine(CONFIG.DB_PATH)
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        self.session = Session()
        logger.info("Backend with database is ready.")

    def shutdown(self):
        self.session.close()

    def get_dirs(self):
        dirs = []

        # Collect directories
        for root, _, _ in os.walk(CONFIG.ROOT_DIR):
            dirs.append(root)

        logger.info(f"Found {len(dirs)} directories.")
        return dirs

    def get_genres(self):
        query = self.session.query(Genres).all()
        genres = [genre.name for genre in query]
        return genres

    def add_genre(self, name):
        genre = self.session.query(Genres).filter_by(name=name).first()
        if not genre:
            genre = Genres(name=name)
            self.session.add(genre)
            self.session.commit()
            logger.info(f"Genre '{genre}' was added.")
        else:
            logger.warning(f"Genre with name '{name}' is already in database!")

    def remove_genre(self, name):
        genre = self.session.query(Genres).filter_by(name=name).first()
        if genre:
            self.session.delete(genre)
            self.session.commit()
            logger.info(f"Genre '{genre}' was removed.")
        else:
            logger.warning(f"Genre with name '{name}' is not in database!")

    def get_tracks(self, path):
        query = self.session.query(Tracks).filter(Tracks.path.startswith(path)).all()
        tracks = [track.__dict__ for track in query]

        for track in tracks:
            # Drop SQLAlchemy key
            track.pop("_sa_instance_state")

            # Convert genre-ids to genre-names
            genres = ""
            genre_ids = track["genres"]
            if ";" in genre_ids:
                genre_ids = genre_ids.split(";")
            else:
                genre_ids = list(genre_ids)

            for genre_id in genre_ids:
                genre = self.session.query(Genres).filter_by(id=genre_id).first()
                if genre:
                    genres += genre.name + ", "
                else:
                    logger.warning(f"Genre with ID '{genre_id}' was not found!")

            if len(genres) > 0:
                genres = genres[:-2]
            track["genres"] = genres

            # Convert length
            length = track["length"]
            track["length"] = f"{int(length / 60)}:{int(length % 60)}"

        logger.info(f"Loaded {len(tracks)} tracks.")
        return tracks

    def import_tracks(self, path, progress):
        progress.value = 0
        all_files = []

        # Collect files
        for root, _, files in os.walk(path):
            for file in files:
                all_files.append(os.path.join(root, file))

        # Process files
        for i, file in enumerate(all_files):
            file_base = os.path.basename(file)
            track = self.session.query(Tracks).filter_by(path=file).first()

            # Track is not imported yet and has valid audio-type
            if not track:
                if file_base.split(".")[-1] in CONFIG.AUDIO_TYPES:
                    metadata = extract_metadata(file)

                    track = Tracks(title=metadata["title"],
                                   artist=metadata["artist"],
                                   genres=[],
                                   length=metadata["length"],
                                   path=file)
                    self.session.add(track)
                    logger.info(f"Track '{track}' was imported.")
                else:
                    logger.warning(f"Track with path '{file_base}' has no valid audio-type!")
            else:
                logger.info(f"Track with path '{file_base}' is already imported.")

            # Update progressbar
            if i % len(all_files) == 10:
                progress.value = i / len(all_files)

        self.session.commit()
        progress.value = 100

    def reload_tracks(self, path, progress):
        progress.value = 0
        tracks = self.session.query(Tracks).filter(Tracks.path.startswith(path)).all()

        for i, track in enumerate(tracks):
            metadata = extract_metadata(track.path)
            track.title = metadata["title"]
            track.artist = metadata["artist"]
            track.length = metadata["length"]
            logger.info(f"Track '{track}' was updated.")

            # Update progressbar
            if i % len(tracks) == 10:
                progress.value = i / len(tracks)

        self.session.commit()
        progress.value = 100
