"""final schema sprint 6

Revision ID: b84da2c08d1a
Revises: 57cdd7262cef
Create Date: 2026-08-25 13:17:21.955446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b84da2c08d1a"
down_revision: Union[str, Sequence[str], None] = "57cdd7262cef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    generation_status_enum = postgresql.ENUM(
        "GENERATED",
        "NEEDS_CLARIFICATION",
        "FAILED",
        name="generationstatus",
    )

    generation_status_enum.create(op.get_bind(), checkfirst=True)

    # Remove the old VARCHAR default before changing the column type.
    op.alter_column(
        "applicant_document_drafts",
        "generation_status",
        server_default=None,
    )

    # Convert VARCHAR -> PostgreSQL ENUM.
    op.alter_column(
        "applicant_document_drafts",
        "generation_status",
        existing_type=sa.VARCHAR(length=50),
        type_=generation_status_enum,
        nullable=False,
        postgresql_using="generation_status::text::generationstatus",
    )

    # Restore the default using the new ENUM type.
    op.alter_column(
        "applicant_document_drafts",
        "generation_status",
        server_default=sa.text("'GENERATED'::generationstatus"),
    )

    # Add self-referencing foreign key for draft lineage/versioning.
    op.create_foreign_key(
        "fk_applicant_document_drafts_source_draft_id",
        "applicant_document_drafts",
        "applicant_document_drafts",
        ["source_draft_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "fk_applicant_document_drafts_source_draft_id",
        "applicant_document_drafts",
        type_="foreignkey",
    )

    generation_status_enum = postgresql.ENUM(
        "GENERATED",
        "NEEDS_CLARIFICATION",
        "FAILED",
        name="generationstatus",
    )

    op.alter_column(
        "applicant_document_drafts",
        "generation_status",
        existing_type=generation_status_enum,
        type_=sa.VARCHAR(length=50),
        nullable=True,
        existing_server_default=sa.text("'generated'::character varying"),
        postgresql_using="generation_status::text::varchar",
    )

    generation_status_enum.drop(op.get_bind(), checkfirst=True)