from __future__ import annotations

import csv
import io
import os
from collections.abc import Sequence

from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpResponse

from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import ContextService
from apps.sprints.constants import SprintDataImportStatus, SprintDataImportType
from apps.sprints.models import SprintDataImport, SprintDataImportRow
from apps.teams.models import Team


class BaseSprintDataImportService(ContextService):
    IMPORT_TYPE: str = ""
    MAX_FILE_SIZE_MB: int = 10
    REQUIRED_COLUMNS: list[str] = [
        "Story Type",
        "Jira ID",
        "Title",
        "Assignee",
        "Efforts",
        "Sprint",
        "Label",
        "Mapping",
    ]
    SAMPLE_ROW: list[str] = [
        "Story",
        "JIRA-123",
        "Example Story",
        "user@example.com",
        "3600",
        "Sprint 1",
        "sample-label",
        "PROJECT",
    ]
    TEMPLATE_FILENAME: str = "sprint_data_import_template.csv"

    def _get_sprint(self, sprint_code: str):
        from apps.sprints.selectors import get_sprint_by_code

        sprint = get_sprint_by_code(sprint_code)
        if sprint is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )
        return sprint

    def _get_team(self, team_code: str) -> Team:
        try:
            return Team.objects.get(code=team_code, is_active=True)
        except Team.DoesNotExist as exc:
            raise NotFoundException(
                resource="Team", lookup_field="code", lookup_value=team_code
            ) from exc

    def _validate_file(self, file) -> None:
        _, ext = os.path.splitext(file.name)
        if ext.lower().lstrip(".") != "csv":
            raise ValidationException("Only CSV files are accepted.")
        file_size_mb = file.size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValidationException(
                f"File too large. Maximum allowed size: {self.MAX_FILE_SIZE_MB} MB."
            )

    def _validate_columns(self, fieldnames: Sequence[str] | None) -> None:
        actual = set(fieldnames or [])
        missing = set(self.REQUIRED_COLUMNS) - actual
        if missing:
            raise ValidationException(
                f"Missing required column(s): {', '.join(sorted(missing))}."
            )

    def _next_version(self, sprint_id: int, team_id: int) -> int:
        last = (
            SprintDataImport.objects.filter(
                sprint_id=sprint_id,
                team_id=team_id,
                import_type=self.IMPORT_TYPE,
            )
            .order_by("-version_number")
            .values_list("version_number", flat=True)
            .first()
        )
        return (last or 0) + 1

    @transaction.atomic
    def upload(self, sprint_code: str, team_code: str, file) -> SprintDataImport:
        self._validate_file(file)
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        self._validate_columns(reader.fieldnames)

        sprint = self._get_sprint(sprint_code)
        team = self._get_team(team_code)
        version = self._next_version(sprint.pk, team.pk)

        # Supersede any active record for this sprint/team/type combo
        SprintDataImport.objects.filter(
            sprint=sprint,
            team=team,
            import_type=self.IMPORT_TYPE,
            status=SprintDataImportStatus.ACTIVE,
        ).update(status=SprintDataImportStatus.SUPERSEDED)

        record = SprintDataImport.objects.create(
            sprint=sprint,
            team=team,
            import_type=self.IMPORT_TYPE,
            version_number=version,
            file_name=file.name,
            status=SprintDataImportStatus.ACTIVE,
            created_by=self.user,
            updated_by=self.user,
        )

        col_map = {
            "Story Type": "story_type",
            "Jira ID": "jira_id",
            "Title": "title",
            "Assignee": "assignee",
            "Efforts": "efforts",
            "Sprint": "sprint",
            "Label": "label",
            "Mapping": "mapping",
        }

        rows_data = list(reader)

        # Collect unique values for batch FK lookups
        assignee_vals: set[str] = set()
        label_vals: set[str] = set()
        mapping_vals: set[str] = set()
        sprint_vals: set[str] = set()
        for csv_row in rows_data:
            if v := (csv_row.get("Assignee") or "").strip():
                assignee_vals.add(v)
            if v := (csv_row.get("Label") or "").strip():
                label_vals.add(v)
            if v := (csv_row.get("Mapping") or "").strip():
                mapping_vals.add(v)
            if v := (csv_row.get("Sprint") or "").strip():
                sprint_vals.add(v)

        from apps.projects.models.label import ProjectLabel
        from apps.recharges.models import RechargeType
        from apps.sprints.models.sprint import Sprint
        from apps.users.models import UserProfile

        user_map: dict[str, UserProfile] = {
            p.user.email: p
            for p in UserProfile.objects.select_related("user").filter(
                user__email__in=assignee_vals
            )
        }

        label_map: dict[str, ProjectLabel] = {}
        for lbl in ProjectLabel.objects.filter(label__in=label_vals).order_by("pk"):
            label_map.setdefault(lbl.label, lbl)

        mapping_map: dict[str, RechargeType] = {}
        for rt in RechargeType.objects.filter(name__in=mapping_vals).order_by("pk"):
            mapping_map.setdefault(rt.name, rt)

        sprint_map: dict[str, Sprint] = {}
        for s in Sprint.objects.filter(name__in=sprint_vals).order_by("pk"):
            sprint_map.setdefault(s.name, s)

        for csv_row in rows_data:
            assignee_val = (csv_row.get("Assignee") or "").strip()
            label_val = (csv_row.get("Label") or "").strip()
            mapping_val = (csv_row.get("Mapping") or "").strip()
            sprint_val = (csv_row.get("Sprint") or "").strip()
            SprintDataImportRow.objects.create(
                import_record=record,
                created_by=self.user,
                updated_by=self.user,
                **{field: csv_row.get(col, "") or "" for col, field in col_map.items()},
                assignee_code=user_map.get(assignee_val),
                label_code=label_map.get(label_val),
                mapping_code=mapping_map.get(mapping_val),
                sprint_code=sprint_map.get(sprint_val),
            )

        return record

    def list_imports(
        self, sprint_code: str, team_code: str
    ) -> QuerySet[SprintDataImport]:
        from apps.sprints.selectors import get_imports_for_sprint_team

        sprint = self._get_sprint(sprint_code)
        team = self._get_team(team_code)
        return get_imports_for_sprint_team(
            sprint_id=sprint.pk,
            team_id=team.pk,
            import_type=self.IMPORT_TYPE,
        )

    def get_template_response(self) -> HttpResponse:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.REQUIRED_COLUMNS)
        writer.writerow(self.SAMPLE_ROW)
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{self.TEMPLATE_FILENAME}"'
        )
        return response

    def _resolve_fk_objects(
        self,
        assignee_code_str: str,
        sprint_code_str: str,
        label_code_str: str,
        mapping_code_str: str,
    ) -> tuple:
        """Return (assignee_obj, sprint_obj, label_obj, mapping_obj) by code lookup."""
        from apps.projects.models.label import ProjectLabel
        from apps.recharges.models import RechargeType
        from apps.sprints.models.sprint import Sprint
        from apps.users.models import UserProfile

        assignee_obj = None
        if assignee_code_str:
            try:
                assignee_obj = UserProfile.objects.select_related("user").get(
                    code=assignee_code_str
                )
            except UserProfile.DoesNotExist:
                pass

        sprint_obj = None
        if sprint_code_str:
            try:
                sprint_obj = Sprint.objects.get(code=sprint_code_str)
            except Sprint.DoesNotExist:
                pass

        label_obj = None
        if label_code_str:
            try:
                label_obj = ProjectLabel.objects.get(code=label_code_str)
            except ProjectLabel.DoesNotExist:
                pass

        mapping_obj = None
        if mapping_code_str:
            try:
                mapping_obj = RechargeType.objects.get(code=mapping_code_str)
            except RechargeType.DoesNotExist:
                pass

        return assignee_obj, sprint_obj, label_obj, mapping_obj

    @transaction.atomic
    def create_row(
        self,
        import_code: str,
        story_type: str = "",
        jira_id: str = "",
        title: str = "",
        assignee_code_str: str = "",
        efforts: str = "",
        sprint_code_str: str = "",
        label_code_str: str = "",
        mapping_code_str: str = "",
    ) -> SprintDataImportRow:
        from apps.sprints.selectors import get_import_by_code

        record = get_import_by_code(import_code)
        if record is None:
            raise NotFoundException(
                resource="SprintDataImport",
                lookup_field="code",
                lookup_value=import_code,
            )

        assignee_obj, sprint_obj, label_obj, mapping_obj = self._resolve_fk_objects(
            assignee_code_str, sprint_code_str, label_code_str, mapping_code_str
        )

        # For manual rows: CSV fields are left empty; all values go to override fields.
        # None = no override (use CSV fallback); set a value (even "") to override.
        return SprintDataImportRow.objects.create(
            import_record=record,
            is_manually_added=True,
            story_type_override=story_type or None,
            jira_id_override=jira_id or None,
            title_override=title or None,
            assignee_override=assignee_obj.user.email
            if assignee_obj
            else (assignee_code_str or None),
            efforts_override=efforts or None,
            sprint_override=sprint_obj.name
            if sprint_obj
            else (sprint_code_str or None),
            label_override=label_obj.label if label_obj else (label_code_str or None),
            mapping_override=mapping_obj.name
            if mapping_obj
            else (mapping_code_str or None),
            assignee_code_override=assignee_obj,
            sprint_code_override=sprint_obj,
            label_code_override=label_obj,
            mapping_code_override=mapping_obj,
            created_by=self.user,
            updated_by=self.user,
        )

    @transaction.atomic
    def update_row(
        self,
        row_code: str,
        story_type: str = "",
        jira_id: str = "",
        title: str = "",
        assignee_code_str: str = "",
        efforts: str = "",
        sprint_code_str: str = "",
        label_code_str: str = "",
        mapping_code_str: str = "",
    ) -> SprintDataImportRow:
        try:
            row = SprintDataImportRow.objects.select_related(
                "assignee_code__user", "sprint_code", "label_code", "mapping_code"
            ).get(code=row_code)
        except SprintDataImportRow.DoesNotExist as exc:
            raise NotFoundException(
                resource="SprintDataImportRow",
                lookup_field="code",
                lookup_value=row_code,
            ) from exc

        assignee_obj, sprint_obj, label_obj, mapping_obj = self._resolve_fk_objects(
            assignee_code_str, sprint_code_str, label_code_str, mapping_code_str
        )

        # Only write an override when the submitted value differs from the CSV value.
        # Matching the CSV value clears any existing override and falls back naturally.
        def _text(submitted: str, csv_val: str) -> str | None:
            return None if submitted == csv_val else (submitted or None)

        row.story_type_override = _text(story_type, row.story_type)
        row.jira_id_override = _text(jira_id, row.jira_id)
        row.title_override = _text(title, row.title)
        row.efforts_override = _text(efforts, row.efforts)

        # FK fields: compare submitted code against CSV-resolved FK code.
        csv_assignee = row.assignee_code.code if row.assignee_code else ""
        if assignee_code_str == csv_assignee:
            row.assignee_override = None
            row.assignee_code_override = None
        else:
            row.assignee_override = (
                assignee_obj.user.email if assignee_obj else (assignee_code_str or None)
            )
            row.assignee_code_override = assignee_obj

        csv_sprint = row.sprint_code.code if row.sprint_code else ""
        if sprint_code_str == csv_sprint:
            row.sprint_override = None
            row.sprint_code_override = None
        else:
            row.sprint_override = (
                sprint_obj.name if sprint_obj else (sprint_code_str or None)
            )
            row.sprint_code_override = sprint_obj

        csv_label = row.label_code.code if row.label_code else ""
        if label_code_str == csv_label:
            row.label_override = None
            row.label_code_override = None
        else:
            row.label_override = (
                label_obj.label if label_obj else (label_code_str or None)
            )
            row.label_code_override = label_obj

        csv_mapping = row.mapping_code.code if row.mapping_code else ""
        if mapping_code_str == csv_mapping:
            row.mapping_override = None
            row.mapping_code_override = None
        else:
            row.mapping_override = (
                mapping_obj.name if mapping_obj else (mapping_code_str or None)
            )
            row.mapping_code_override = mapping_obj

        row.updated_by = self.user
        row.save(
            update_fields=[
                "story_type_override",
                "jira_id_override",
                "title_override",
                "assignee_override",
                "efforts_override",
                "sprint_override",
                "label_override",
                "mapping_override",
                "assignee_code_override",
                "sprint_code_override",
                "label_code_override",
                "mapping_code_override",
                "updated_by",
                "updated_at",
            ]
        )
        return row

    def review(self, import_code: str):
        """Run review checks and persist results.

        Returns ``(review, row_results)`` where ``row_results`` maps
        ``row.code → {check_type: pass_bool}``.
        """
        from apps.sprints.engine import SprintDataImportEngine
        from apps.sprints.selectors import get_import_by_code

        record = get_import_by_code(import_code)
        if record is None:
            raise NotFoundException(
                resource="SprintDataImport",
                lookup_field="code",
                lookup_value=import_code,
            )
        return SprintDataImportEngine.run_review(record.pk, user=self.user)

    @transaction.atomic
    def confirm(self, import_code: str, notes: str = ""):
        from apps.sprints.constants import ImportRowCheckStatus
        from apps.sprints.models.sprint_data_import_review import SprintDataImportReview
        from apps.sprints.models.sprint_data_import_review_capacity_result import (
            SprintDataImportReviewCapacityResult,
        )
        from apps.sprints.models.sprint_data_import_review_complete import (
            SprintDataImportReviewComplete,
        )
        from apps.sprints.models.sprint_data_import_review_result import (
            SprintDataImportReviewResult,
        )
        from apps.sprints.selectors import get_import_by_code

        record = get_import_by_code(import_code)
        if record is None:
            raise NotFoundException(
                resource="SprintDataImport",
                lookup_field="code",
                lookup_value=import_code,
            )

        latest_review = (
            SprintDataImportReview.objects.filter(import_record_id=record.pk)
            .order_by("-reviewed_at")
            .first()
        )
        if latest_review is None:
            raise ValidationException(
                "This import has not been reviewed yet. "
                "Please run a review before confirming."
            )

        has_failures = (
            SprintDataImportReviewResult.objects.filter(
                review=latest_review, status=ImportRowCheckStatus.FAIL
            ).exists()
            or SprintDataImportReviewCapacityResult.objects.filter(
                review=latest_review, status=ImportRowCheckStatus.FAIL
            ).exists()
        )

        if has_failures and not notes.strip():
            raise ValidationException(
                "Some checks are failing. Please provide override notes to confirm."
            )

        completion, _ = SprintDataImportReviewComplete.objects.update_or_create(
            sprint=record.sprint,
            import_type=record.import_type,
            defaults={
                "review": latest_review,
                "completed_by": self.user,
                "override_applied": has_failures,
                "override_notes": notes.strip(),
            },
        )

        # Promote the import record to CONFIRMED status
        record.status = SprintDataImportStatus.CONFIRMED
        record.updated_by = self.user
        record.save(update_fields=["status", "updated_by", "updated_at"])

        return completion

    @transaction.atomic
    def delete_row(self, row_code: str) -> None:
        try:
            row = SprintDataImportRow.objects.get(code=row_code)
        except SprintDataImportRow.DoesNotExist as exc:
            raise NotFoundException(
                resource="SprintDataImportRow",
                lookup_field="code",
                lookup_value=row_code,
            ) from exc

        if row.is_manually_added:
            row.delete()
        else:
            row.is_deleted = True
            row.updated_by = self.user
            row.save(update_fields=["is_deleted", "updated_by", "updated_at"])


class SprintDataImportForecastService(BaseSprintDataImportService):
    IMPORT_TYPE = SprintDataImportType.FORECAST
    TEMPLATE_FILENAME = "sprint_forecast_template.csv"


class SprintDataImportActualService(BaseSprintDataImportService):
    IMPORT_TYPE = SprintDataImportType.ACTUAL
    TEMPLATE_FILENAME = "sprint_actuals_template.csv"
