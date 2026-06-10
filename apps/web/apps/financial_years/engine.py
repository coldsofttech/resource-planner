from datetime import date

from apps.configurations.selectors import FinancialYear as FYConfig


class FinancialYearEngine:
    @staticmethod
    def days_remaining(end_date: date | None) -> int:
        if not end_date:
            return 0
        return (end_date - date.today()).days

    @staticmethod
    def in_threshold(end_date: date | None) -> bool:
        if not end_date:
            return False
        try:
            warning_days = FYConfig.get_fy_expiry_warning_days()
        except Exception:
            warning_days = 30
        return FinancialYearEngine.days_remaining(end_date) <= warning_days
