# app/models/pathway.py
from sqlalchemy import Column, String, Text, Integer, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel

class PathwayStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

   

class StepStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ImmigrationPathway(BaseModel):
    __tablename__ = "immigration_pathways"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    country = Column(String(100), nullable=False, default="Canada")
    icon = Column(
        String(255),
        nullable=True,
    )

    color = Column(
        String(20),
        nullable=True,
    )

    category = Column(
        String(100),
        index=True,
        nullable=False,
    )

    status = Column(
        Enum(
            PathwayStatus,
            values_callable=lambda enum_class: [member.value for member in enum_class],
            name="pathwaystatus",
        ),
        default=PathwayStatus.DRAFT,
        nullable=False,
    )
    version = Column(Integer, default=1, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    steps = relationship("RoadmapStep", back_populates="pathway", order_by="RoadmapStep.step_order")
    user_roadmaps = relationship("UserRoadmap", back_populates="pathway")

class RoadmapStep(BaseModel):
    __tablename__ = "roadmap_steps"
    
    pathway_id = Column(UUID(as_uuid=True), ForeignKey("immigration_pathways.id"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(
        String(255),
        index=True,
        nullable=False,
    )
    description = Column(Text, nullable=True)
    step_order = Column(
        Integer,
        index=True,
        nullable=False,
    )
    

    estimated_duration_days = Column(
        Integer,
        nullable=True,
    )
    is_required = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    pathway = relationship("ImmigrationPathway", back_populates="steps")
    user_steps = relationship("UserRoadmapStep", back_populates="roadmap_step")

class UserRoadmapStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class UserRoadmap(BaseModel):
    __tablename__ = "user_roadmaps"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    pathway_id = Column(
        UUID(as_uuid=True),
        ForeignKey("immigration_pathways.id"),
        nullable=False,
    )

    status = Column(
        Enum(
            UserRoadmapStatus,
            values_callable=lambda enum_class: [member.value for member in enum_class],
            name="userroadmapstatus",
        ),
        default=UserRoadmapStatus.ACTIVE,
        nullable=False,
    )

    pathway = relationship(
        "ImmigrationPathway",
        back_populates="user_roadmaps",
    )

    steps = relationship(
        "UserRoadmapStep",
        back_populates="user_roadmap",
    )


class UserRoadmapStep(BaseModel):
    __tablename__ = "user_roadmap_steps"
    
    user_roadmap_id = Column(UUID(as_uuid=True), ForeignKey("user_roadmaps.id"), nullable=False)
    roadmap_step_id = Column(UUID(as_uuid=True), ForeignKey("roadmap_steps.id"), nullable=False)
    status = Column(
    Enum(
        StepStatus,
        values_callable=lambda enum_class: [member.value for member in enum_class],
        name="stepstatus",
    ),
    default=StepStatus.PENDING,
    nullable=False,
)
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes = Column(Text, nullable=True)
    
    # Relationships
    user_roadmap = relationship("UserRoadmap", back_populates="steps")
    roadmap_step = relationship("RoadmapStep", back_populates="user_steps")