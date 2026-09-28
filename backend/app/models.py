import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func


Base = declarative_base()


# =========================================================
# PROJECT
# =========================================================

class Project(Base):
    __tablename__ = "projects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    business_name = Column(
        String,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    industry = Column(
        String,
        nullable=False,
    )

    style = Column(
        String,
        nullable=False,
    )

    generation_palette = Column(
        String,
        nullable=True,
    )

    generation_custom_colors = Column(
        Text,
        nullable=True,
    )

    generation_logo_style = Column(
        String,
        nullable=True,
    )

    generation_creative_prompt = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    assets = relationship(
        "Asset",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    brand_kit = relationship(
        "BrandKit",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )


# =========================================================
# ASSET
# =========================================================

class Asset(Base):
    __tablename__ = "assets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    asset_type = Column(
        String,
        nullable=False,
    )

    url = Column(
        Text,
        nullable=False,
    )

    prompt = Column(
        Text,
        nullable=True,
    )

    specification = Column(
        Text,
        nullable=True,
    )

    is_selected = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project = relationship(
        "Project",
        back_populates="assets",
    )


# =========================================================
# BRAND KIT
# =========================================================

class BrandKit(Base):
    __tablename__ = "brand_kits"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # -----------------------------------------------------
    # COLORS
    # -----------------------------------------------------

    primary_color = Column(
        String,
        nullable=False,
        default="#000000",
    )

    secondary_color = Column(
        String,
        nullable=False,
        default="#FFFFFF",
    )

    accent_color = Column(
        String,
        nullable=False,
        default="#6366F1",
    )

    # -----------------------------------------------------
    # AI BRAND STRATEGY
    # -----------------------------------------------------

    slogan = Column(
        Text,
        nullable=True,
    )

    personality = Column(
        Text,
        nullable=True,
    )

    tone = Column(
        Text,
        nullable=True,
    )

    target_audience = Column(
        Text,
        nullable=True,
    )

    marketing_message = Column(
        Text,
        nullable=True,
    )

    heading_font = Column(
        String,
        nullable=True,
    )

    body_font = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project = relationship(
        "Project",
        back_populates="brand_kit",
    )
