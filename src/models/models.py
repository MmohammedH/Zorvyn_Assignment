from datetime import UTC, date, datetime

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clients.db.connection import Base
from constants import DatabaseConstants
from enums.enums import RecordCategory, RecordType, UserRole


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(DatabaseConstants.USER_EMAIL_MAX_LENGTH),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(DatabaseConstants.USER_NAME_MAX_LENGTH),
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(DatabaseConstants.USER_PASSWORD_MAX_LENGTH),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(DatabaseConstants.USER_ROLE_MAX_LENGTH),
        nullable=False,
        default=UserRole.VIEWER.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    financial_records: Mapped[list["FinancialRecord"]] = relationship(
        "FinancialRecord",
        back_populates="created_by",
        lazy="select",
    )


class FinancialRecord(Base):
    __tablename__ = "financial_record"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    created_by_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(
            precision=DatabaseConstants.AMOUNT_PRECISION,
            scale=DatabaseConstants.AMOUNT_SCALE,
        ),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(DatabaseConstants.RECORD_TYPE_MAX_LENGTH),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(DatabaseConstants.RECORD_CATEGORY_MAX_LENGTH),
        nullable=False,
        index=True,
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(
        String(DatabaseConstants.RECORD_NOTES_MAX_LENGTH),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    created_by: Mapped["User"] = relationship("User", back_populates="financial_records")
