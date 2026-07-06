from decimal import Decimal

from django.test import SimpleTestCase

from apps.resource_plans.constants import Progression, RampPattern
from apps.resource_plans.services.placeholder_leave import PlaceholderLeaveService
from apps.resource_plans.services.ramp_distribution import RampDistributionService


class FakeSprint:
    def __init__(self, sprint_id: int) -> None:
        self.id = sprint_id


class FakeSegment:
    def __init__(
        self,
        segment_order,
        duration,
        start_percentage,
        end_percentage,
        progression=str(Progression.LINEAR),
        step_count=None,
    ):
        self.segment_order = segment_order
        self.duration = duration
        self.start_percentage = start_percentage
        self.end_percentage = end_percentage
        self.progression = progression
        self.step_count = step_count


class PlaceholderLeaveServiceRoundHalfTest(SimpleTestCase):
    def test_rounds_up_to_nearest_half(self):
        self.assertEqual(
            PlaceholderLeaveService._round_half(Decimal("2.3")), Decimal("2.5")
        )

    def test_rounds_down_to_nearest_half(self):
        self.assertEqual(
            PlaceholderLeaveService._round_half(Decimal("2.2")), Decimal("2.0")
        )

    def test_exact_half_boundary_rounds_up(self):
        self.assertEqual(
            PlaceholderLeaveService._round_half(Decimal("2.25")), Decimal("2.5")
        )

    def test_already_a_half_increment_unchanged(self):
        self.assertEqual(
            PlaceholderLeaveService._round_half(Decimal("3.5")), Decimal("3.5")
        )

    def test_zero_stays_zero(self):
        self.assertEqual(
            PlaceholderLeaveService._round_half(Decimal("0")), Decimal("0")
        )


class PlaceholderLeaveServiceDistributeDaysTest(SimpleTestCase):
    def test_empty_sprint_caps_returns_empty_dict(self):
        result = PlaceholderLeaveService._distribute_days(Decimal("5"), [])
        self.assertEqual(result, {})

    def test_zero_total_days_returns_empty_dict(self):
        s1 = FakeSprint(1)
        result = PlaceholderLeaveService._distribute_days(
            Decimal("0"), [(s1, Decimal("10"))]
        )
        self.assertEqual(result, {})

    def test_even_split_under_cap(self):
        s1, s2 = FakeSprint(1), FakeSprint(2)
        result = PlaceholderLeaveService._distribute_days(
            Decimal("4"), [(s1, Decimal("10")), (s2, Decimal("10"))]
        )
        self.assertEqual(result, {1: Decimal("2"), 2: Decimal("2")})
        self.assertEqual(sum(result.values()), Decimal("4"))

    def test_low_cap_sprint_spills_leftover_to_other_sprints(self):
        s1, s2 = FakeSprint(1), FakeSprint(2)
        # Equal share would be 3 each, but s1 only has room for 1.
        result = PlaceholderLeaveService._distribute_days(
            Decimal("6"), [(s1, Decimal("1")), (s2, Decimal("10"))]
        )
        self.assertEqual(result[1], Decimal("1"))
        self.assertEqual(sum(result.values()), Decimal("6"))

    def test_zero_capacity_sprint_excluded_from_allocation(self):
        s1, s2 = FakeSprint(1), FakeSprint(2)
        result = PlaceholderLeaveService._distribute_days(
            Decimal("4"), [(s1, Decimal("0")), (s2, Decimal("10"))]
        )
        self.assertNotIn(1, result)
        self.assertEqual(result[2], Decimal("4"))

    def test_total_exceeding_all_capacity_allocates_only_up_to_cap(self):
        s1, s2 = FakeSprint(1), FakeSprint(2)
        result = PlaceholderLeaveService._distribute_days(
            Decimal("100"), [(s1, Decimal("2")), (s2, Decimal("3"))]
        )
        self.assertEqual(sum(result.values()), Decimal("5"))


class RampDistributionServiceZeroInputTest(SimpleTestCase):
    def test_zero_total_days_returns_zeros(self):
        result = RampDistributionService.distribute(
            Decimal("0"), 3, str(RampPattern.FLAT), None, None
        )
        self.assertEqual(result, [Decimal("0")] * 3)

    def test_zero_sprint_count_returns_empty_list(self):
        result = RampDistributionService.distribute(
            Decimal("10"), 0, str(RampPattern.FLAT), None, None
        )
        self.assertEqual(result, [])


class RampDistributionServicePatternShapeTest(SimpleTestCase):
    def test_flat_splits_evenly(self):
        result = RampDistributionService.distribute(
            Decimal("8"), 4, str(RampPattern.FLAT), None, None
        )
        self.assertEqual(result, [Decimal("2")] * 4)

    def test_ramp_up_is_non_decreasing(self):
        result = RampDistributionService.distribute(
            Decimal("20"), 4, str(RampPattern.RAMP_UP), None, None
        )
        self.assertEqual(result, sorted(result))
        self.assertLess(result[0], result[-1])

    def test_ramp_down_is_non_increasing(self):
        result = RampDistributionService.distribute(
            Decimal("20"), 4, str(RampPattern.RAMP_DOWN), None, None
        )
        self.assertEqual(result, sorted(result, reverse=True))
        self.assertGreater(result[0], result[-1])

    def test_ramp_up_down_peaks_in_the_middle(self):
        result = RampDistributionService.distribute(
            Decimal("20"), 5, str(RampPattern.RAMP_UP_DOWN), None, None
        )
        peak_index = result.index(max(result))
        self.assertEqual(peak_index, 2)
        self.assertLessEqual(result[0], result[1])
        self.assertLessEqual(result[-1], result[-2])

    def test_ramp_up_steady_plateaus_after_initial_ramp(self):
        result = RampDistributionService.distribute(
            Decimal("60"), 6, str(RampPattern.RAMP_UP_STEADY), None, None
        )
        # Ramps for the first n//3 sprints, then holds steady — allow up to
        # one 0.25 quantum of drift from the total-preservation correction.
        self.assertLessEqual(abs(result[-1] - result[-2]), Decimal("0.25"))
        self.assertLessEqual(abs(result[-2] - result[-3]), Decimal("0.25"))

    def test_steady_down_plateaus_before_final_decline(self):
        result = RampDistributionService.distribute(
            Decimal("60"), 6, str(RampPattern.STEADY_DOWN), None, None
        )
        self.assertLessEqual(abs(result[0] - result[1]), Decimal("0.25"))
        self.assertLessEqual(abs(result[1] - result[2]), Decimal("0.25"))
        self.assertLess(result[-1], result[0])

    def test_stepped_is_non_decreasing_in_discrete_blocks(self):
        result = RampDistributionService.distribute(
            Decimal("40"), 8, str(RampPattern.STEPPED), None, None
        )
        self.assertEqual(result, sorted(result))

    def test_all_values_are_multiples_of_quarter_day(self):
        for pattern in [
            RampPattern.FLAT,
            RampPattern.RAMP_UP,
            RampPattern.RAMP_DOWN,
            RampPattern.RAMP_UP_DOWN,
            RampPattern.RAMP_UP_STEADY,
            RampPattern.STEADY_DOWN,
            RampPattern.STEPPED,
        ]:
            result = RampDistributionService.distribute(
                Decimal("17"), 5, str(pattern), None, None
            )
            for day in result:
                self.assertEqual(
                    day % Decimal("0.25"),
                    Decimal("0"),
                    f"{pattern}: {day} is not a 0.25 multiple",
                )

    def test_sum_preserved_without_cap(self):
        for pattern in [
            RampPattern.FLAT,
            RampPattern.RAMP_UP,
            RampPattern.RAMP_DOWN,
            RampPattern.RAMP_UP_DOWN,
            RampPattern.RAMP_UP_STEADY,
            RampPattern.STEADY_DOWN,
            RampPattern.STEPPED,
        ]:
            result = RampDistributionService.distribute(
                Decimal("17"), 5, str(pattern), None, None
            )
            self.assertEqual(sum(result), Decimal("17"), f"{pattern} lost total")


class RampDistributionServiceCappingTest(SimpleTestCase):
    def test_flat_cap_redistributes_to_preserve_total(self):
        result = RampDistributionService.distribute(
            Decimal("12"), 4, str(RampPattern.FLAT), None, Decimal("2")
        )
        self.assertTrue(all(d <= Decimal("2") for d in result))
        self.assertEqual(sum(result), Decimal("8"))

    def test_ramp_up_cap_does_not_redistribute(self):
        result = RampDistributionService.distribute(
            Decimal("20"), 4, str(RampPattern.RAMP_UP), None, Decimal("3")
        )
        self.assertTrue(all(d <= Decimal("3") for d in result))
        self.assertLess(sum(result), Decimal("20"))

    def test_no_cap_returns_unclamped_values(self):
        result = RampDistributionService.distribute(
            Decimal("20"), 2, str(RampPattern.RAMP_UP), None, None
        )
        self.assertEqual(sum(result), Decimal("20"))


class RampDistributionServiceSegmentDrivenTest(SimpleTestCase):
    def test_linear_segment_interpolates_from_start_to_end(self):
        segment = FakeSegment(
            segment_order=1,
            duration=5,
            start_percentage=Decimal("0"),
            end_percentage=Decimal("100"),
            progression=str(Progression.LINEAR),
        )
        result = RampDistributionService.distribute(
            Decimal("100"), 5, str(RampPattern.CUSTOM), [segment], None
        )
        self.assertEqual(result, sorted(result))
        self.assertLess(result[0], result[-1])

    def test_flat_progression_holds_constant_share(self):
        segment = FakeSegment(
            segment_order=1,
            duration=4,
            start_percentage=Decimal("10"),
            end_percentage=Decimal("90"),
            progression=str(Progression.FLAT),
        )
        result = RampDistributionService.distribute(
            Decimal("40"), 4, str(RampPattern.CUSTOM), [segment], None
        )
        self.assertEqual(result, [Decimal("10")] * 4)

    def test_multiple_segments_concatenate_in_order(self):
        seg1 = FakeSegment(
            segment_order=2,
            duration=2,
            start_percentage=Decimal("0"),
            end_percentage=Decimal("0"),
            progression=str(Progression.FLAT),
        )
        seg2 = FakeSegment(
            segment_order=1,
            duration=2,
            start_percentage=Decimal("100"),
            end_percentage=Decimal("100"),
            progression=str(Progression.FLAT),
        )
        # seg2 (order=1) should be consumed before seg1 (order=2) regardless
        # of the order they're passed in.
        result = RampDistributionService.distribute(
            Decimal("40"), 4, str(RampPattern.CUSTOM), [seg1, seg2], None
        )
        self.assertEqual(
            result, [Decimal("20"), Decimal("20"), Decimal("0"), Decimal("0")]
        )

    def test_exponential_progression_is_concave_up(self):
        segment = FakeSegment(
            segment_order=1,
            duration=5,
            start_percentage=Decimal("0"),
            end_percentage=Decimal("100"),
            progression=str(Progression.EXPONENTIAL),
        )
        result = RampDistributionService.distribute(
            Decimal("100"), 5, str(RampPattern.CUSTOM), [segment], None
        )
        # Later increments should be larger than earlier ones for a t^2 curve.
        first_gap = result[1] - result[0]
        last_gap = result[-1] - result[-2]
        self.assertGreater(last_gap, first_gap)

    def test_stepped_progression_produces_discrete_levels(self):
        segment = FakeSegment(
            segment_order=1,
            duration=8,
            start_percentage=Decimal("0"),
            end_percentage=Decimal("100"),
            progression=str(Progression.STEPPED),
            step_count=4,
        )
        result = RampDistributionService.distribute(
            Decimal("80"), 8, str(RampPattern.CUSTOM), [segment], None
        )
        distinct_levels = sorted(set(result))
        self.assertLessEqual(len(distinct_levels), 4)
