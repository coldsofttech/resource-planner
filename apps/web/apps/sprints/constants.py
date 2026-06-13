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
