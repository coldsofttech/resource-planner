class ReportVisualization:
    TABLE = "table"
    CARD = "card"
    BAR = "bar"
    LINE = "line"
    PIE = "pie"

    CHOICES = [
        (TABLE, "Table"),
        (CARD, "KPI Cards"),
        (BAR, "Bar Chart"),
        (LINE, "Line Chart"),
        (PIE, "Pie Chart"),
    ]


class SharePermission:
    VIEW = "view"
    EDIT = "edit"

    CHOICES = [
        (VIEW, "View"),
        (EDIT, "Edit"),
    ]


class FilterOperator:
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    IN = "in"
    NOT_IN = "not_in"

    CHOICES = [
        (EQ, "Equals"),
        (NEQ, "Not Equals"),
        (GT, "Greater Than"),
        (GTE, "Greater Than or Equal"),
        (LT, "Less Than"),
        (LTE, "Less Than or Equal"),
        (CONTAINS, "Contains"),
        (STARTS_WITH, "Starts With"),
        (ENDS_WITH, "Ends With"),
        (IS_NULL, "Is Empty"),
        (IS_NOT_NULL, "Is Not Empty"),
        (IN, "Is Any Of"),
        (NOT_IN, "Is Not Any Of"),
    ]


class AggregationFunction:
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"

    CHOICES = [
        (COUNT, "Count"),
        (COUNT_DISTINCT, "Count Distinct"),
        (SUM, "Sum"),
        (AVG, "Average"),
        (MIN, "Minimum"),
        (MAX, "Maximum"),
    ]


class FieldType:
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    CHOICE = "choice"
