from django.db.models import Count, Q, QuerySet

from apps.products.models import Product


def get_all_products() -> QuerySet[Product]:
    return Product.objects.select_related(
        "business_unit", "created_by", "updated_by"
    ).all()


def get_active_products() -> QuerySet[Product]:
    return Product.objects.select_related(
        "business_unit", "created_by", "updated_by"
    ).filter(is_active=True)


def get_product_by_code(code: str) -> Product | None:
    try:
        return Product.objects.select_related(
            "business_unit", "created_by", "updated_by"
        ).get(code=code)
    except Product.DoesNotExist:
        return None


def product_name_exists(
    name: str, business_unit_id: int, exclude_pk: int | None = None
) -> bool:
    qs = Product.objects.filter(name=name, business_unit_id=business_unit_id)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_product_stats() -> dict:
    return Product.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )
