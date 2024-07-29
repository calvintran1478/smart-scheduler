from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from litestar.contrib.sqlalchemy.base import UUIDBase
import enum

class TagColourEnum(str, enum.Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"

class Tag(UUIDBase):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tags_user_id_name"),)

    name: Mapped[str]
    colour: Mapped[str] = mapped_column(Enum(TagColourEnum, name="tag_colour"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="tags")
    tasks: Mapped[list["Task"]] = relationship(back_populates="tag")