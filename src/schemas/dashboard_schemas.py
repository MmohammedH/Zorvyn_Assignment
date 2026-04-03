from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    total_income: float = Field(..., description="Sum of all income records")
    total_expenses: float = Field(..., description="Sum of all expense records")
    net_balance: float = Field(..., description="total_income - total_expenses")
    total_records: int = Field(..., description="Total number of financial records")
    income_records: int = Field(..., description="Number of income records")
    expense_records: int = Field(..., description="Number of expense records")


class CategoryTotal(BaseModel):
    category: str
    type: str
    total: float
    count: int


class CategoryBreakdownResponse(BaseModel):
    breakdown: list[CategoryTotal]


class MonthlyTrend(BaseModel):
    year: int
    month: int
    month_label: str = Field(..., description="E.g. '2024-03'")
    total_income: float
    total_expenses: float
    net: float


class TrendResponse(BaseModel):
    months: list[MonthlyTrend]
    period_months: int


class RecentRecord(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    record_date: str
    notes: str | None
    created_by_name: str


class RecentActivityResponse(BaseModel):
    records: list[RecentRecord]
    total_shown: int
