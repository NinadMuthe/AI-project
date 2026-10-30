"""Add monthly budget tracking without removing existing data."""
from alembic import op
import sqlalchemy as sa

revision = "9c2e4d7a1b10"
down_revision = "056cf66f0553"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("budgets", sa.Column("month", sa.String(length=7), nullable=True))
    op.execute("UPDATE budgets SET month = to_char(CURRENT_DATE, 'YYYY-MM') WHERE month IS NULL")
    op.alter_column("budgets", "month", nullable=False)
    op.create_unique_constraint("uq_budget_user_category_month", "budgets", ["user_id", "category", "month"])


def downgrade() -> None:
    op.drop_constraint("uq_budget_user_category_month", "budgets", type_="unique")
    op.drop_column("budgets", "month")
