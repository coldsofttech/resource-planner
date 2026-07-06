from __future__ import annotations

import csv
import io
import os

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.business_units.selectors import get_business_unit_by_code
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import (
    AuditableService,
    ExportService,
    FilterableQueryService,
    ImportService,
)
from apps.products import selectors
from apps.products.models import Product


class ProductService(AuditableService, FilterableQueryService):
    _MODULE = "products"
    _RESOURCE_TYPE = "product"

    filterable_fields: dict[str, str] = {"bu": "business_unit__code"}
    search_fields: list[str] = ["name", "short_name"]
    sortable_fields: list[str] = ["name", "short_name", "is_active", "created_at"]
    default_ordering: list[str] = ["business_unit__name", "name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_products()

    def _snapshot(self, product: Product) -> dict:
        return {
            "code": product.code,
            "name": product.name,
            "short_name": product.short_name,
            "business_unit": product.business_unit.code,
            "is_active": product.is_active,
        }

    def get(self, code: str, *args, **kwargs) -> Product:
        obj = selectors.get_product_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Product", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        short_name: str,
        business_unit_code: str,
        is_active: bool = True,
    ) -> Product:
        bu = get_business_unit_by_code(business_unit_code)
        if bu is None:
            raise NotFoundException(
                resource="Business Unit",
                lookup_field="code",
                lookup_value=business_unit_code,
            )
        if selectors.product_name_exists(name, bu.pk):
            raise AlreadyExistsException(
                detail=f"A product named '{name}' already exists in this business unit."
            )
        product = Product.objects.create(
            name=name,
            short_name=short_name,
            business_unit=bu,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=product.code,
            after=self._snapshot(product),
            actor=self.user,
        )
        return product

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Product:
        product = self.get(code=code)
        before = self._snapshot(product)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "name" in kwargs:
            new_name = kwargs["name"]
            if new_name != product.name and selectors.product_name_exists(
                new_name, product.business_unit_id, exclude_pk=product.pk
            ):
                raise AlreadyExistsException(
                    detail=(
                        f"A product named '{new_name}' already exists "
                        "in this business unit."
                    )
                )
            product.name = new_name
            update_fields.append("name")

        if "short_name" in kwargs:
            product.short_name = kwargs["short_name"]
            update_fields.append("short_name")

        if "business_unit_code" in kwargs:
            bu = get_business_unit_by_code(kwargs["business_unit_code"])
            if bu is None:
                raise NotFoundException(
                    resource="Business Unit",
                    lookup_field="code",
                    lookup_value=kwargs["business_unit_code"],
                )
            if selectors.product_name_exists(
                product.name, bu.pk, exclude_pk=product.pk
            ):
                raise AlreadyExistsException(
                    detail=(
                        f"A product named '{product.name}' already exists "
                        "in this business unit."
                    )
                )
            product.business_unit = bu
            update_fields.append("business_unit")

        if "is_active" in kwargs:
            product.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        product.updated_by = self.user
        product.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=product.code,
            before=before,
            after=self._snapshot(product),
            actor=self.user,
        )
        return product

    @transaction.atomic
    def activate(self, code: str) -> Product:
        product = self.get(code=code)
        if not product.is_active:
            before = self._snapshot(product)
            product.is_active = True
            product.updated_by = self.user
            product.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=product.code,
                before=before,
                after=self._snapshot(product),
                actor=self.user,
            )
        return product

    @transaction.atomic
    def deactivate(self, code: str) -> Product:
        product = self.get(code=code)
        if product.is_active:
            before = self._snapshot(product)
            product.is_active = False
            product.updated_by = self.user
            product.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=product.code,
                before=before,
                after=self._snapshot(product),
                actor=self.user,
            )
        return product

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        product = self.get(code=code)
        product_code = product.code
        before = self._snapshot(product)
        product.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=product_code,
            before=before,
            actor=self.user,
        )

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_product_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats

    def options(self) -> list[dict]:
        return [
            {
                "code": p.code,
                "name": p.name,
                "business_unit_code": p.business_unit.code,
                "business_unit_name": p.business_unit.name,
            }
            for p in selectors.get_active_products()
        ]


class ProductImportService(ImportService):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 1_000
    MAX_IMPORT_FILE_SIZE_MB = 5

    def validate_file(self, file) -> None:
        _, ext = os.path.splitext(file.name)
        if ext.lower().lstrip(".") not in self.SUPPORTED_IMPORT_FORMATS:
            raise ValidationException(
                "Unsupported file format. Allowed: "
                f"{', '.join(self.SUPPORTED_IMPORT_FORMATS)}."
            )
        file_size_mb = file.size / (1024 * 1024)
        if file_size_mb > self.MAX_IMPORT_FILE_SIZE_MB:
            raise ValidationException(
                "File too large. Maximum allowed size: "
                f"{self.MAX_IMPORT_FILE_SIZE_MB} MB."
            )

    def validate_row(self, row: dict, row_num: int) -> list[dict]:
        errors: list[dict] = []
        name = (row.get("name") or "").strip()
        short_name = (row.get("short_name") or "").strip()
        business_unit_code = (row.get("business_unit_code") or "").strip()

        if not name:
            errors.append(
                {"row": row_num, "field": "name", "message": "Name is required."}
            )
        elif len(name) > 255:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Name must be 255 characters or fewer.",
                }
            )

        if not short_name:
            errors.append(
                {
                    "row": row_num,
                    "field": "short_name",
                    "message": "Short name is required.",
                }
            )
        elif len(short_name) > 10:
            errors.append(
                {
                    "row": row_num,
                    "field": "short_name",
                    "message": "Short name must be 10 characters or fewer.",
                }
            )

        if not business_unit_code:
            errors.append(
                {
                    "row": row_num,
                    "field": "business_unit_code",
                    "message": "Business unit code is required.",
                }
            )

        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"name", "short_name", "business_unit_code"}
        actual_columns = set(reader.fieldnames or [])
        missing = required_columns - actual_columns
        if missing:
            raise ValidationException(
                f"Missing required column(s): {', '.join(sorted(missing))}."
            )

        rows = list(reader)
        if len(rows) > self.MAX_IMPORT_ROWS:
            raise ValidationException(
                f"Too many rows. Maximum allowed: {self.MAX_IMPORT_ROWS}."
            )

        total = len(rows)
        created_rows: list[dict] = []
        errors: list[dict] = []
        product_svc = ProductService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            short_name = row["short_name"].strip()
            business_unit_code = row["business_unit_code"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")

            bu = get_business_unit_by_code(business_unit_code)
            if bu is None:
                errors.append(
                    {
                        "row": row_num,
                        "field": "business_unit_code",
                        "message": f"Business unit '{business_unit_code}' not found.",
                    }
                )
                continue

            if selectors.product_name_exists(name, bu.pk):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": (
                            f"A product named '{name}' already exists "
                            "in this business unit."
                        ),
                    }
                )
                continue

            if not dry_run:
                product_svc.create(
                    name=name,
                    short_name=short_name,
                    business_unit_code=business_unit_code,
                    is_active=is_active,
                )

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class ProductExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Name",
        "short_name": "Short Name",
        "business_unit": "Business Unit",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "name",
        "short_name",
        "business_unit",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "products_export"
    EXPORT_MODULE_NAME = "Products"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = selectors.get_all_products()
        if filters:
            bu_code = (filters.get("bu") or "").strip()
            if bu_code:
                qs = qs.filter(business_unit__code=bu_code)

            is_active_raw = filters.get("is_active")
            if is_active_raw in (None, ""):
                qs = qs.filter(is_active=True)
            elif str(is_active_raw).lower() != "all":
                qs = qs.filter(
                    is_active=str(is_active_raw).lower() not in ("false", "0")
                )

            search = (filters.get("search") or "").strip()
            if search:
                qs = qs.filter(name__icontains=search)

        rows = self._prepare_rows(list(qs), resolved)

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            "Allowed: csv, xlsx, pdf, json."
        )
