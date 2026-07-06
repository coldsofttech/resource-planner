import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.audit.services import AuditService
from apps.recharges.models import Recharge, RechargeDetail, RechargeType

logger = logging.getLogger(__name__)

_MODULE = "recharges"


def _recharge_snapshot(instance: Recharge) -> dict:
    return {
        "code": instance.code,
        "sprint_id": instance.sprint_id,
        "type": instance.type,
        "programme_id": instance.programme_id,
        "project_id": instance.project_id,
        "recharge_type_id": instance.recharge_type_id,
        "total_days": str(instance.total_days),
        "total_cost": str(instance.total_cost),
    }


def _recharge_detail_snapshot(instance: RechargeDetail) -> dict:
    return {
        "code": instance.code,
        "sprint_id": instance.sprint_id,
        "team_id": instance.team_id,
        "type": instance.type,
        "jira_id": instance.jira_id,
        "total_days": str(instance.total_days),
        "total_cost": str(instance.total_cost),
    }


@receiver(post_save, sender=Recharge)
def audit_recharge_save(sender, instance, created, update_fields=None, **kwargs):
    is_code_update = update_fields is not None and set(update_fields) == {"code"}
    if not is_code_update:
        return
    AuditService.log_create(
        module=_MODULE,
        resource_type="recharge",
        resource_code=instance.code,
        after=_recharge_snapshot(instance),
    )


@receiver(post_delete, sender=Recharge)
def audit_recharge_delete(sender, instance, **kwargs):
    AuditService.log_delete(
        module=_MODULE,
        resource_type="recharge",
        resource_code=instance.code,
        before=_recharge_snapshot(instance),
    )


@receiver(post_save, sender=RechargeDetail)
def audit_recharge_detail_save(sender, instance, created, update_fields=None, **kwargs):
    is_code_update = update_fields is not None and set(update_fields) == {"code"}
    if not is_code_update:
        return
    AuditService.log_create(
        module=_MODULE,
        resource_type="recharge_detail",
        resource_code=instance.code,
        after=_recharge_detail_snapshot(instance),
    )


@receiver(post_delete, sender=RechargeDetail)
def audit_recharge_detail_delete(sender, instance, **kwargs):
    AuditService.log_delete(
        module=_MODULE,
        resource_type="recharge_detail",
        resource_code=instance.code,
        before=_recharge_detail_snapshot(instance),
    )


@receiver(post_save, sender=RechargeType)
def log_recharge_type_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s recharge type: %s (%s).", action, instance.name, instance.code)


@receiver(post_delete, sender=RechargeType)
def log_recharge_type_delete(sender, instance, **kwargs):
    logger.debug("Deleted recharge type: %s (%s).", instance.name, instance.code)
