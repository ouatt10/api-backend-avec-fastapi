from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, Numeric, DateTime,  UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Tontine(Base):
    __tablename__ = "tontines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    contribution_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    number_of_rounds: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="CREATED")

    members = relationship("Member", back_populates="tontine")
    rounds = relationship("Round", back_populates="tontine")


class Member(Base):
    __tablename__ = "members"

    __table_args__ = (
        UniqueConstraint(
            "tontine_id",
            "position",
            name="uq_member_position_per_tontine"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tontine_id: Mapped[int] = mapped_column(ForeignKey("tontines.id"))
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    position: Mapped[int] = mapped_column(Integer)

    tontine = relationship("Tontine", back_populates="members")


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    tontine_id: Mapped[int] = mapped_column(ForeignKey("tontines.id"))
    round_number: Mapped[int] = mapped_column(Integer)
    beneficiary_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tontine = relationship("Tontine", back_populates="rounds")


class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)