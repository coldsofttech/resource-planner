"""Query execution engine for the Custom Report builder.

Turns a `(data_source, visualization, config)` triple into an executable
Django queryset and shapes the result for the requested visualization.
Data sources and their field definitions live in `apps.reports.data_sources`
— this module only knows how to turn that declarative registry plus a
report's `config` into rows.

`config` shape (all keys optional unless noted):
    fields:  list[str]   — dotted field paths to project (table) or group by
                           (table+values, bar/line axis, pie dimension)
    filters: list[dict]  — [{"field", "operator", "value"}, ...]
    values:  list[dict]  — [{"field", "aggregation"}, ...] aggregated metrics
    axis:    str          — bar/line grouping dimension (falls back to fields[0])
    legend:  str | None   — optional secondary grouping for multi-series bar/line
    sort_by: list[dict]  — [{"field", "direction"}, ...] direction: asc|desc
"""

from __future__ import annotations

from typing import Any

from django.db.models import Avg, Count, Max, Min, Q, QuerySet, Sum

from apps.core.exceptions import ValidationException
from apps.reports.constants import (
    AggregationFunction,
    FilterOperator,
    ReportVisualization,
)
from apps.reports.data_sources import DataSource, ReportField, get_data_source

MAX_TABLE_ROWS = 5000
MAX_CHART_SERIES = 12
MAX_CARDS = 6

_AGG_BUILDERS = {
    AggregationFunction.COUNT: lambda f: Count(f),
    AggregationFunction.COUNT_DISTINCT: lambda f: Count(f, distinct=True),
    AggregationFunction.SUM: lambda f: Sum(f),
    AggregationFunction.AVG: lambda f: Avg(f),
    AggregationFunction.MIN: lambda f: Min(f),
    AggregationFunction.MAX: lambda f: Max(f),
}


def _agg_alias(field_key: str, aggregation: str) -> str:
    return f"{field_key.replace('__', '_')}_{aggregation}"


def _require_field(ds: DataSource, field_key: str) -> ReportField:
    field_def = ds.get_field(field_key)
    if field_def is None:
        raise ValidationException(
            f"Unknown field '{field_key}' for data source '{ds.key}'."
        )
    return field_def


def _operator_q(field_key: str, operator: str, value: Any) -> Q:
    if operator == FilterOperator.EQ:
        return Q(**{field_key: value})
    if operator == FilterOperator.NEQ:
        return ~Q(**{field_key: value})
    if operator == FilterOperator.GT:
        return Q(**{f"{field_key}__gt": value})
    if operator == FilterOperator.GTE:
        return Q(**{f"{field_key}__gte": value})
    if operator == FilterOperator.LT:
        return Q(**{f"{field_key}__lt": value})
    if operator == FilterOperator.LTE:
        return Q(**{f"{field_key}__lte": value})
    if operator == FilterOperator.CONTAINS:
        return Q(**{f"{field_key}__icontains": value})
    if operator == FilterOperator.STARTS_WITH:
        return Q(**{f"{field_key}__istartswith": value})
    if operator == FilterOperator.ENDS_WITH:
        return Q(**{f"{field_key}__iendswith": value})
    if operator == FilterOperator.IS_NULL:
        return Q(**{f"{field_key}__isnull": True})
    if operator == FilterOperator.IS_NOT_NULL:
        return Q(**{f"{field_key}__isnull": False})
    if operator == FilterOperator.IN:
        return Q(**{f"{field_key}__in": value if isinstance(value, list) else [value]})
    if operator == FilterOperator.NOT_IN:
        return ~Q(**{f"{field_key}__in": value if isinstance(value, list) else [value]})
    raise ValidationException(f"Unsupported filter operator '{operator}'.")


def _apply_filters(ds: DataSource, qs: QuerySet, filters: list[dict]) -> QuerySet:
    q = Q()
    for flt in filters:
        field_key = flt.get("field")
        operator = flt.get("operator")
        if not isinstance(field_key, str) or not isinstance(operator, str):
            raise ValidationException("Each filter requires 'field' and 'operator'.")
        field_def = _require_field(ds, field_key)
        if not field_def.filterable:
            raise ValidationException(f"Field '{field_key}' is not filterable.")
        q &= _operator_q(field_key, operator, flt.get("value"))
    return qs.filter(q) if filters else qs


def _build_annotations(ds: DataSource, values: list[dict]) -> dict[str, Any]:
    if not values:
        raise ValidationException("At least one aggregated value is required.")
    annotations: dict[str, Any] = {}
    for value in values:
        field_key = value.get("field")
        aggregation = value.get("aggregation")
        if not isinstance(field_key, str) or not isinstance(aggregation, str):
            raise ValidationException(
                "Each aggregated value requires 'field' and 'aggregation'."
            )
        field_def = _require_field(ds, field_key)
        if aggregation not in _AGG_BUILDERS:
            raise ValidationException(f"Unsupported aggregation '{aggregation}'.")
        if (
            aggregation
            not in (AggregationFunction.COUNT, AggregationFunction.COUNT_DISTINCT)
            and not field_def.aggregatable
        ):
            raise ValidationException(
                f"Field '{field_key}' does not support '{aggregation}'."
            )
        alias = _agg_alias(field_key, aggregation)
        if alias in annotations:
            raise ValidationException(
                f"Duplicate aggregated value for '{field_key}' ({aggregation})."
            )
        annotations[alias] = _AGG_BUILDERS[aggregation](field_key)
    return annotations


def _apply_sort(qs: QuerySet, sort_by: list[dict], allowed_keys: set[str]) -> QuerySet:
    order: list[str] = []
    for entry in sort_by or []:
        field_key = entry.get("field")
        if field_key not in allowed_keys:
            continue
        prefix = "-" if entry.get("direction") == "desc" else ""
        order.append(f"{prefix}{field_key}")
    return qs.order_by(*order) if order else qs


def _base_queryset(ds: DataSource, config: dict) -> QuerySet:
    model = ds.get_model()
    qs = model.objects.all()
    for base_filter in ds.base_filters:
        qs = qs.filter(
            _operator_q(
                base_filter["field"], base_filter["operator"], base_filter.get("value")
            )
        )
    return _apply_filters(ds, qs, config.get("filters") or [])


def table_columns(ds: DataSource, config: dict) -> list[dict]:
    """Column key/label pairs a `table` visualization of `config` would
    produce, without executing any query — used for export column specs."""
    fields = config.get("fields") or []
    values = config.get("values") or []
    columns = []
    for fk in fields:
        field_def = ds.get_field(fk)
        if field_def is not None:
            columns.append({"key": fk, "label": field_def.label})
    for value in values:
        field_key = value.get("field")
        aggregation = value.get("aggregation")
        if not isinstance(field_key, str) or not isinstance(aggregation, str):
            continue
        field_def = ds.get_field(field_key)
        if field_def is None or aggregation not in dict(AggregationFunction.CHOICES):
            continue
        alias = _agg_alias(field_key, aggregation)
        agg_label = dict(AggregationFunction.CHOICES)[aggregation]
        columns.append({"key": alias, "label": f"{field_def.label} ({agg_label})"})
    return columns


def _build_table(ds: DataSource, qs: QuerySet, config: dict) -> dict:
    fields = config.get("fields") or []
    values = config.get("values") or []
    if not fields and not values:
        raise ValidationException("Select at least one field or aggregated value.")

    for field_key in fields:
        field_def = _require_field(ds, field_key)
        if values and not field_def.groupable:
            raise ValidationException(f"Field '{field_key}' cannot be grouped.")

    columns = table_columns(ds, config)

    if values:
        annotations = _build_annotations(ds, values)
        qs = qs.values(*fields).annotate(**annotations)
        allowed = set(fields) | set(annotations)
        qs = _apply_sort(qs, config.get("sort_by") or [], allowed)
        rows = list(qs[:MAX_TABLE_ROWS])
    else:
        allowed = set(fields)
        qs = _apply_sort(qs, config.get("sort_by") or [], allowed)
        rows = list(qs.values(*fields)[:MAX_TABLE_ROWS])

    return {
        "type": ReportVisualization.TABLE,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": len(rows) >= MAX_TABLE_ROWS,
    }


def _build_cards(ds: DataSource, qs: QuerySet, config: dict) -> dict:
    values = (config.get("values") or [])[:MAX_CARDS]
    if not values:
        raise ValidationException("Select at least one aggregated value.")

    annotations = _build_annotations(ds, values)
    result = qs.aggregate(**annotations)

    cards = []
    for value in values:
        alias = _agg_alias(value["field"], value["aggregation"])
        field_def = _require_field(ds, value["field"])
        agg_label = dict(AggregationFunction.CHOICES)[value["aggregation"]]
        cards.append(
            {
                "label": f"{field_def.label} ({agg_label})",
                "value": result.get(alias),
            }
        )
    return {"type": ReportVisualization.CARD, "cards": cards}


def _build_series(ds: DataSource, qs: QuerySet, config: dict) -> dict:
    axis = config.get("axis") or (config.get("fields") or [None])[0]
    if not axis:
        raise ValidationException("An axis field is required for this visualization.")
    axis_def = _require_field(ds, axis)
    if not axis_def.groupable:
        raise ValidationException(f"Field '{axis}' cannot be used as an axis.")

    legend = config.get("legend")
    if legend:
        legend_def = _require_field(ds, legend)
        if not legend_def.groupable:
            raise ValidationException(f"Field '{legend}' cannot be used as a legend.")

    values = config.get("values") or []
    if len(values) != 1:
        raise ValidationException(
            "Exactly one aggregated value is required for chart visualizations."
        )
    annotations = _build_annotations(ds, values)
    metric_alias = next(iter(annotations))

    group_fields = [axis, legend] if legend else [axis]
    qs = qs.values(*group_fields).annotate(**annotations)
    qs = _apply_sort(qs, config.get("sort_by") or [], {axis, metric_alias})
    rows = list(qs[:MAX_TABLE_ROWS])

    labels: list[str] = []
    seen_labels: set[str] = set()
    for row in rows:
        label = str(row[axis])
        if label not in seen_labels:
            seen_labels.add(label)
            labels.append(label)

    if legend:
        series_keys: list[str] = []
        seen_series: set[str] = set()
        for row in rows:
            key = str(row[legend])
            if key not in seen_series:
                seen_series.add(key)
                series_keys.append(key)
        series_keys = series_keys[:MAX_CHART_SERIES]
        matrix = {(str(r[axis]), str(r[legend])): r[metric_alias] for r in rows}
        series = [
            {
                "label": key,
                "data": [matrix.get((label, key)) for label in labels],
            }
            for key in series_keys
        ]
    else:
        by_label = {str(r[axis]): r[metric_alias] for r in rows}
        field_def = _require_field(ds, values[0]["field"])
        agg_label = dict(AggregationFunction.CHOICES)[values[0]["aggregation"]]
        series = [
            {
                "label": f"{field_def.label} ({agg_label})",
                "data": [by_label.get(label) for label in labels],
            }
        ]

    return {"type": "chart", "labels": labels, "series": series}


def _build_pie(ds: DataSource, qs: QuerySet, config: dict) -> dict:
    axis = config.get("axis") or (config.get("fields") or [None])[0]
    if not axis:
        raise ValidationException("A dimension field is required for a pie chart.")
    axis_def = _require_field(ds, axis)
    if not axis_def.groupable:
        raise ValidationException(f"Field '{axis}' cannot be used as a dimension.")

    values = config.get("values") or []
    if len(values) != 1:
        raise ValidationException("Exactly one aggregated value is required.")
    annotations = _build_annotations(ds, values)
    metric_alias = next(iter(annotations))

    qs = qs.values(axis).annotate(**annotations)
    qs = _apply_sort(qs, config.get("sort_by") or [], {axis, metric_alias})
    rows = list(qs[:MAX_CHART_SERIES])

    return {
        "type": ReportVisualization.PIE,
        "labels": [str(r[axis]) for r in rows],
        "values": [r[metric_alias] for r in rows],
    }


def execute(data_source_key: str, visualization: str, config: dict) -> dict:
    ds = get_data_source(data_source_key)
    if ds is None:
        raise ValidationException(f"Unknown data source '{data_source_key}'.")

    qs = _base_queryset(ds, config)

    if visualization == ReportVisualization.TABLE:
        return _build_table(ds, qs, config)
    if visualization == ReportVisualization.CARD:
        return _build_cards(ds, qs, config)
    if visualization in (ReportVisualization.BAR, ReportVisualization.LINE):
        result = _build_series(ds, qs, config)
        result["visualization"] = visualization
        return result
    if visualization == ReportVisualization.PIE:
        return _build_pie(ds, qs, config)
    raise ValidationException(f"Unsupported visualization '{visualization}'.")
