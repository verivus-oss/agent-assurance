"""Hand-derived accepted and rejected values for the explicit predicates."""
from _test_require import require
from _ascii_predicates import matches_decimal_id, split_closure_root, valid_abstraction_id, valid_assertion_id, valid_date, valid_datetime, valid_digest, valid_header_name, valid_observed_line, valid_operation, valid_rfc3339_utc_shape, valid_scheme, valid_semver, valid_upper_prefix

def test_decimal_identifiers() -> None:
    for value in ('U0', 'U01', 'U01a'):
        require(matches_decimal_id('U', True, value), value)
    for value in ('U', 'U01A', 'U01aa', 'U-1', 'X01', 'U١'):
        require(not matches_decimal_id('U', True, value), value)
    require(matches_decimal_id('A', False, 'A12'))
    require(not matches_decimal_id('A', False, 'A12a'))

def test_metadata_shapes() -> None:
    require(valid_semver('0.1.99'))
    require(not valid_semver('01.1.99'))
    require(valid_date('2026-10-27'))
    require(not valid_date('2026-1-27'))
    require(valid_datetime('2026-10-27T12:34:56Z'))
    require(not valid_datetime('2026-10-27T12:34:56'))
    require(valid_upper_prefix('EV_1'))
    require(not valid_upper_prefix('Ev_1'))

def test_bound_values() -> None:
    require(valid_digest('sha256:' + 'a' * 64))
    require(not valid_digest('sha256:' + 'A' * 64))
    require(split_closure_root('sha384:' + 'b' * 96) == ('sha384', 'b' * 96))
    require(split_closure_root('sha384:' + 'g' * 96) is None)
    require(valid_abstraction_id('component.v0'))
    require(not valid_abstraction_id('component.v١'))
    require(valid_assertion_id('A-1_x'))
    require(not valid_assertion_id('A-_x'))
    require(valid_observed_line('A-1 = observed(a=b)'))
    require(not valid_observed_line('A-1 = observed()'))
    require(valid_header_name('x-api-key'))
    require(not valid_header_name('x-api-key: secret'))
    require(valid_operation('apply_1'))
    require(not valid_operation('Apply_1'))
    require(valid_scheme('git+ssh'))
    require(not valid_scheme('Git+ssh'))
    require(valid_rfc3339_utc_shape('2026-10-27T12:34:56.123Z'))
    require(not valid_rfc3339_utc_shape('2026-10-27T12:34:56.1234567890Z'))
if __name__ == '__main__':
    test_decimal_identifiers()
    test_metadata_shapes()
    test_bound_values()
    print('ASCII predicates: 3 test groups passed')
