import functools

from fastapi import status, HTTPException
from sqlalchemy import create_engine, select, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError

from logger.logger import log
from config.config_loader import ConfigLoader
from models.platform import Platform
from models.rom import Rom


class DBHandler:
    def __init__(self) -> None:
        self.engine = create_engine(ConfigLoader.get_db_engine(), pool_pre_ping=True)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)

    @staticmethod
    def retry(func):
        @functools.wraps(func)
        def wrapper(*args):
            return func(*args)

        return wrapper

    @staticmethod
    def raise_error(e: Exception):
        log.critical(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    # ========= Platforms =========
    def add_platform(self, platform: Platform):
        try:
            with self.session.begin() as session:
                session.merge(platform)
        except ProgrammingError as e:
            self.raise_error(e)

    def get_platforms(self):
        try:
            with self.session.begin() as session:
                return session.scalars(
                    select(Platform).order_by(Platform.slug.asc())
                ).all()
        except ProgrammingError as e:
            self.raise_error(e)

    def get_platform(self, slug: str):
        try:
            with self.session.begin() as session:
                return session.scalars(select(Platform).filter_by(slug=slug)).first()
        except ProgrammingError as e:
            self.raise_error(e)

    def purge_platforms(self, platforms: list[str]):
        try:
            with self.session.begin() as session:
                session.query(Platform).filter(
                    or_(Platform.fs_slug.not_in(platforms), Platform.fs_slug.is_(None))
                ).delete(synchronize_session="evaluate")
        except ProgrammingError as e:
            self.raise_error(e)

    # ========= Roms =========
    def add_rom(self, rom: Rom):
        try:
            with self.session.begin() as session:
                session.merge(rom)
        except ProgrammingError as e:
            self.raise_error(e)

    def get_roms(self, p_slug: str):
        try:
            return select(Rom).filter_by(p_slug=p_slug).order_by(Rom.file_name.asc())
        except ProgrammingError as e:
            self.raise_error(e)

    def get_rom(self, id):
        try:
            with self.session.begin() as session:
                return session.get(Rom, id)
        except ProgrammingError as e:
            self.raise_error(e)

    def update_rom(self, id: int, data: dict):
        try:
            with self.session.begin() as session:
                session.query(Rom).filter(Rom.id == id).update(
                    data, synchronize_session="evaluate"
                )
        except ProgrammingError as e:
            self.raise_error(e)

    def delete_rom(self, id: int):
        try:
            with self.session.begin() as session:
                session.query(Rom).filter(Rom.id == id).delete(
                    synchronize_session="evaluate"
                )
        except ProgrammingError as e:
            self.raise_error(e)

    def purge_roms(self, p_slug: str, roms: list[list[str]]):
        try:
            with self.session.begin() as session:
                session.query(Rom).filter(
                    Rom.p_slug == p_slug, Rom.file_name.not_in(roms)
                ).delete(synchronize_session="evaluate")
        except ProgrammingError as e:
            self.raise_error(e)

    def update_n_roms(self, p_slug: str):
        try:
            with self.session.begin() as session:
                session.query(Platform).filter_by(slug=p_slug).update(
                    {
                        Platform.n_roms: len(
                            session.query(Rom).filter_by(p_slug=p_slug).all()
                        )
                    },
                    synchronize_session="evaluate",
                )
        except ProgrammingError as e:
            self.raise_error(e)

    # ==== Utils ======
    def rom_exists(self, p_slug: str, file_name: str):
        try:
            with self.session.begin() as session:
                rom = session.scalar(
                    select(Rom).filter_by(p_slug=p_slug, file_name=file_name)
                )
                return rom.id if rom else 0
        except ProgrammingError as e:
            self.raise_error(e)
