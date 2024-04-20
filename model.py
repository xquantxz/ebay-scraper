from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy import select

class Base(DeclarativeBase):
    ...

class WatchedTerm(Base):
    __tablename__ = "watched_term"
    id: Mapped[int] = mapped_column(primary_key=True)
    max_price: Mapped[float]
    max_likes: Mapped[int]
    url: Mapped[str]

    def __repr__(self) -> str:
        return f"WatchedTerm(id={self.id}, url={self.url}, max_price={self.max_price}, max_likes={self.max_likes})"

