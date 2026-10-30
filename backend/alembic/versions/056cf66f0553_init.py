"""Create FinPulse core tables without dropping existing data."""
from alembic import op
import sqlalchemy as sa

revision = "056cf66f0553"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("full_name", sa.String(), nullable=False), sa.Column("email", sa.String(), nullable=False, unique=True), sa.Column("hashed_password", sa.String(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")))
    op.create_table("transactions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("transaction_type", sa.Enum("INCOME", "EXPENSE", name="transactiontype"), nullable=False), sa.Column("category", sa.String(), nullable=False), sa.Column("merchant", sa.String()), sa.Column("description", sa.String()), sa.Column("transaction_date", sa.DateTime(), nullable=False), sa.Column("source", sa.String(), nullable=False, server_default="manual"), sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"))
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_table("budgets", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("category", sa.String(), nullable=False), sa.Column("limit_amount", sa.Numeric(12, 2), nullable=False), sa.Column("month", sa.String(7), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")), sa.CheckConstraint("limit_amount > 0", name="ck_budgets_limit_positive"), sa.UniqueConstraint("user_id", "category", "month", name="uq_budget_user_category_month"))
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])


def downgrade() -> None:
    op.drop_table("budgets")
    op.drop_table("transactions")
    op.drop_table("users")
