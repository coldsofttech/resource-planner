from pycore.types import ListParams, PaginatedResult, Pagination, SortParam

# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestPagination:
    def test_stores_all_fields(self):
        p = Pagination(
            total_count=100,
            total_pages=5,
            current_page=2,
            page_size=20,
            has_next=True,
            has_previous=True,
        )
        assert p.total_count == 100
        assert p.total_pages == 5
        assert p.current_page == 2
        assert p.page_size == 20
        assert p.has_next is True
        assert p.has_previous is True

    def test_has_next_and_has_previous_accept_false(self):
        p = Pagination(
            total_count=5,
            total_pages=1,
            current_page=1,
            page_size=25,
            has_next=False,
            has_previous=False,
        )
        assert p.has_next is False
        assert p.has_previous is False


# ---------------------------------------------------------------------------
# PaginatedResult
# ---------------------------------------------------------------------------


class TestPaginatedResult:
    def _pagination(self) -> Pagination:
        return Pagination(
            total_count=2,
            total_pages=1,
            current_page=1,
            page_size=25,
            has_next=False,
            has_previous=False,
        )

    def test_stores_results_and_pagination(self):
        pagination = self._pagination()
        result = PaginatedResult(results=[1, 2], pagination=pagination)
        assert result.results == [1, 2]
        assert result.pagination is pagination

    def test_results_holds_items_of_any_type(self):
        result = PaginatedResult(results=["a", "b", "c"], pagination=self._pagination())
        assert len(result.results) == 3

    def test_empty_results_list_is_valid(self):
        result = PaginatedResult(results=[], pagination=self._pagination())
        assert result.results == []


# ---------------------------------------------------------------------------
# SortParam
# ---------------------------------------------------------------------------


class TestSortParam:
    def test_default_sort_by_is_id(self):
        assert SortParam().sort_by == "id"

    def test_default_direction_is_asc(self):
        assert SortParam().direction == "asc"

    def test_custom_sort_by_stored(self):
        assert SortParam(sort_by="name").sort_by == "name"

    def test_custom_direction_stored(self):
        assert SortParam(direction="desc").direction == "desc"


# ---------------------------------------------------------------------------
# ListParams
# ---------------------------------------------------------------------------


class TestListParams:
    def test_default_page_is_1(self):
        assert ListParams().page == 1

    def test_default_page_size_is_25(self):
        assert ListParams().page_size == 25

    def test_default_filters_is_empty_dict(self):
        assert ListParams().filters == {}

    def test_filters_not_shared_between_instances(self):
        a, b = ListParams(), ListParams()
        a.filters["x"] = 1
        assert "x" not in b.filters

    def test_default_sorts_contains_one_sort_param(self):
        params = ListParams()
        assert len(params.sorts) == 1
        assert params.sorts[0].sort_by == "id"

    def test_sorts_not_shared_between_instances(self):
        a, b = ListParams(), ListParams()
        a.sorts.append(SortParam(sort_by="name"))
        assert len(b.sorts) == 1

    def test_custom_page_and_page_size(self):
        params = ListParams(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50
