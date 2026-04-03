from enum import Enum


class UserRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class RecordType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class RecordCategory(str, Enum):
    # Income categories
    SALARY = "salary"
    INVESTMENT = "investment"
    FREELANCE = "freelance"
    BONUS = "bonus"
    # Expense categories
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    HOUSING = "housing"
    SHOPPING = "shopping"
    # Shared
    OTHER = "other"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
