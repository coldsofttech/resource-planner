class SprintStatus:
    IN_PROGRESS = "in_progress"
    FUTURE = "future"
    COMPLETED = "completed"
    EXPIRED = "expired"

    CHOICES = [
        (IN_PROGRESS, "In Progress"),
        (FUTURE, "Future"),
        (COMPLETED, "Completed"),
        (EXPIRED, "Expired"),
    ]


class SprintDataImportStatus:
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    SUPERSEDED = "superseded"

    CHOICES = [
        (ACTIVE, "Active"),
        (CONFIRMED, "Confirmed"),
        (SUPERSEDED, "Superseded"),
    ]


class SprintDataImportType:
    ACTUAL = "actual"
    FORECAST = "forecast"

    CHOICES = [
        (ACTUAL, "Actual"),
        (FORECAST, "Forecast"),
    ]


class ImportRowCheck:
    ASSIGNEE = "CHECK_ASSIGNEE"
    SPRINT = "CHECK_SPRINT"
    LABEL = "CHECK_LABEL"
    MAPPING = "CHECK_MAPPING"
    CAPACITY = "CHECK_CAPACITY"

    ALL = [ASSIGNEE, SPRINT, LABEL, MAPPING]
    ALL_WITH_CAPACITY = [ASSIGNEE, SPRINT, LABEL, MAPPING, CAPACITY]

    CHOICES = [
        (ASSIGNEE, "Assignee"),
        (SPRINT, "Sprint"),
        (LABEL, "Label"),
        (MAPPING, "Mapping"),
        (CAPACITY, "Capacity"),
    ]


class ImportRowCheckStatus:
    PASS = "pass"
    FAIL = "fail"

    CHOICES = [
        (PASS, "Pass"),
        (FAIL, "Fail"),
    ]
