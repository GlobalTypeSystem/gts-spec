"""Shared identifier-matching and pattern-coverage corpus (README §10).

Plain data with explicit expected results; no matcher is implemented here. The
same rows drive OP#4 (test_op4_id_match_pattern.py), x-gts-type-ref and
x-gts-instance-ref (test_x_gts_entity_ref.py), and x-gts-pattern-ref
(test_x_gts_pattern_ref.py). test_gts_id_pattern_syntax_unit.py checks the
spelling of every string offline.

- MATCH_CASES: (pattern, candidate, expect), where the candidate is a
  canonical identifier. `expect` states two results: whether the candidate is
  in M(pattern) (OP#4 point matching; entity references also require the
  candidate kind) and whether M(candidate) ⊆ M(pattern) (x-gts-pattern-ref
  coverage). When coverage fails, the candidate itself is the witness: it is
  in M(candidate) but not in M(pattern).
- COVERAGE_CASES: (pattern, candidate, covered, witness), where the candidate
  is a wildcard pattern. OP#4 matches a pattern candidate iff the filter covers
  it. An uncovered row names a canonical witness that the candidate selects
  and the filter does not; a covered row has no witness.
- VALID_PATTERNS / INVALID_PATTERNS: §10 syntax, spelling, length and
  unsigned 32-bit version bounds.
"""

from typing import NamedTuple

import pytest


class Expect(NamedTuple):
    matches: bool  # candidate ∈ M(pattern)
    covered: bool  # M(candidate) ⊆ M(pattern)


IN = Expect(matches=True, covered=True)
OUT = Expect(matches=False, covered=False)

MAX_VERSION = "4294967295"
PREVIOUS_VERSION = "4294967294"
OVERFLOW_VERSION = "4294967296"
UUID = "7a1d2f34-5678-49ab-9012-abcdef123456"
OTHER_UUID = "7a1d2f34-5678-49ab-9012-abcdef123457"

# Names of the README §10 examples.
T = "gts.vendor.package.namespace.type"
I = "acme.package._.instance"

# Names of the README §9.6.2 example.
FAMILY = "gts.x.core.resources.resource.*"
RESOURCE = "gts.x.core.resources.resource.v1~"
BUCKET = RESOURCE + "acme.storage.resources.bucket.v1~"
BUCKET_FAMILY = RESOURCE + "acme.storage.resources.bucket.*"
INSTANCE = BUCKET + "acme.prod._.uploads.v1"
ANONYMOUS = RESOURCE + UUID
OTHER = "gts.x.core.events.event.*"

# The longest valid pattern: 1024 characters, including the `*`.
LONGEST_PATTERN = "gts." + "a" * 1018 + ".*"

# Canonical identifiers have at most 1024 characters (§2.1), so a valid pattern
# can select none of them: then M(p) is empty and every operand covers p. A
# wildcard after the vendor token needs at least `a._.a.v0~` (a first segment
# is a type), one after the version marker at least `0~`. Each pair below sits
# on either side of that bound; witnesses have exactly 1024 characters.
EMPTY_VENDOR_PATTERN = "gts." + "a" * 1011 + ".*"
EMPTY_VENDOR_COMPLETION = "gts." + "a" * 1011 + ".a._.a.v0~"
VENDOR_PATTERN = "gts." + "a" * 1010 + ".*"
VENDOR_WITNESS = "gts." + "a" * 1010 + ".a._.a.v0~"
EMPTY_VERSION_PATTERN = "gts." + "a" * 1011 + ".b.c.d.v*"
EMPTY_VERSION_COMPLETION = "gts." + "a" * 1011 + ".b.c.d.v0~"
VERSION_PATTERN = "gts." + "a" * 1010 + ".b.c.d.v*"
VERSION_WITNESS = "gts." + "a" * 1010 + ".b.c.d.v0~"

# At 1024 characters a minor wildcard can select instances, but its type
# marker would exceed the identifier length limit.
_MINOR_WILDCARD_END = ".b.c.d.v0.*"
_MINOR_BOUNDARY_NAME = "a" * (1024 - len(RESOURCE) - len(_MINOR_WILDCARD_END))
MINOR_BOUNDARY_INSTANCE = RESOURCE + _MINOR_BOUNDARY_NAME + ".b.c.d.v0"
MINOR_BOUNDARY_WILDCARD = MINOR_BOUNDARY_INSTANCE + ".*"


def _table(name, patterns, candidates):
    """One candidate table shared by equivalent patterns (README §10 lists
    such patterns together)."""
    return [
        pytest.param(pattern, candidate, expect, id=f"{name}{suffix}-{case}")
        for suffix, pattern in patterns
        for case, candidate, expect in candidates
    ]


MATCH_CASES = (
    # README §10 "Type identifiers, with and without a wildcard".
    *_table(
        "type",
        [("", T + ".v1~"), ("_chain", T + ".v1~*")],
        [
            ("self", T + ".v1~", IN),
            ("explicit_minor", T + ".v1.0~", IN),
            ("other_minor", T + ".v1.2~", IN),
            ("derived_type", T + ".v1.0~acme.package._.derived.v1.0~", IN),
            ("instance", T + ".v1.0~" + I + ".v1", IN),
            ("uuid_instance", T + ".v1~" + UUID, IN),
            ("other_major", T + ".v2.0~", OUT),
            ("other_major_omitted_minor", T + ".v2~", OUT),
            ("major_digit_boundary", T + ".v10~", OUT),
            ("major_digit_boundary_instance", T + ".v10~" + I + ".v1", OUT),
            ("type_token_boundary", T + "_extra.v1~", OUT),
            ("type_token_boundary_instance", T + "_extra.v1~" + I + ".v1", OUT),
        ],
    ),
    # README §10: `type.*` and `type.v*` include all major versions.
    *_table(
        "all_majors",
        [("", T + ".*"), ("_version_marker", T + ".v*")],
        [
            ("v1", T + ".v1~", IN),
            ("v2_explicit_minor", T + ".v2.0~", IN),
            ("v0", T + ".v0~", IN),
            ("instance", T + ".v3~" + I + ".v1", IN),
            ("type_token_boundary", T + "_extra.v1~", OUT),
            ("type_token_boundary_instance", T + "_extra.v1~" + I + ".v1", OUT),
        ],
    ),
    # README §10 "An explicit minor is required only in the segment containing
    # `v1.*`": later versions are unconstrained.
    *_table(
        "first_minor_wildcard",
        [("", T + ".v1.*")],
        [
            ("explicit_minor", T + ".v1.0~", IN),
            ("omitted_minor", T + ".v1~", OUT),
            ("instance_omitted_minor", T + ".v1.0~" + I + ".v1", IN),
            ("later_versions_unconstrained", T + ".v1.0~" + I + ".v2.3", IN),
            ("derived_type", T + ".v1.0~acme.package._.derived.v1~", IN),
            ("first_omitted_under_instance", T + ".v1~" + I + ".v1", OUT),
            ("later_minor_does_not_count", T + ".v1~" + I + ".v1.2", OUT),
            ("other_major", T + ".v2.0~" + I + ".v1", OUT),
        ],
    ),
    # README §10 "Pinning the minor of a type".
    *_table(
        "pinned_minor",
        [("", T + ".v1.0~"), ("_chain", T + ".v1.0~*")],
        [
            ("same_minor", T + ".v1.0~", IN),
            ("omitted_minor", T + ".v1~", OUT),
            ("other_minor", T + ".v1.1~", OUT),
            ("later_versions_unconstrained", T + ".v1.0~" + I + ".v2.3", IN),
        ],
    ),
    *_table(
        "pinned_minor_2",
        [("", "gts.x.core.resources.resource.v1.2~")],
        [
            ("self", "gts.x.core.resources.resource.v1.2~", IN),
            ("minor_digit_boundary", "gts.x.core.resources.resource.v1.20~", OUT),
            (
                "minor_digit_boundary_instance",
                "gts.x.core.resources.resource.v1.20~acme.prod._.uploads.v1",
                OUT,
            ),
            ("other_minor", "gts.x.core.resources.resource.v1.3~", OUT),
            ("omitted_minor", RESOURCE, OUT),
        ],
    ),
    # README §10: the same version rules apply to major zero.
    *_table(
        "v0_chain",
        [("", T + ".v0~*")],
        [
            ("omitted_minor", T + ".v0~", IN),
            ("explicit_minor", T + ".v0.1~", IN),
            ("instance", T + ".v0~" + I + ".v1", IN),
            ("instance_under_explicit_minor", T + ".v0.1~" + I + ".v1", IN),
            ("other_major", T + ".v1.1~", OUT),
        ],
    ),
    *_table(
        "v0_minor_wildcard",
        [("", T + ".v0.*")],
        [
            ("explicit_minor", T + ".v0.1~", IN),
            ("omitted_minor", T + ".v0~", OUT),
            ("other_major", T + ".v1.2~", OUT),
        ],
    ),
    *_table(
        "v0_pinned",
        [("", T + ".v0.1~*")],
        [("same_minor", T + ".v0.1~", IN), ("other_minor", T + ".v0.2~", OUT)],
    ),
    # README §10 "Concrete instance selectors: minor flexibility in every
    # segment". No textual prefix matching of names, majors or chains.
    *_table(
        "instance",
        [("", T + ".v1~" + I + ".v1")],
        [
            ("self", T + ".v1~" + I + ".v1", IN),
            ("type_minor", T + ".v1.0~" + I + ".v1", IN),
            ("instance_minor", T + ".v1~" + I + ".v1.2", IN),
            ("instance_minor_zero", T + ".v1~" + I + ".v1.0", IN),
            ("independent_minors", T + ".v1.3~" + I + ".v1.2", IN),
            ("major_digit_boundary", T + ".v1~" + I + ".v12", OUT),
            ("other_major", T + ".v1~" + I + ".v2", OUT),
            ("other_type_major", T + ".v2~" + I + ".v1", OUT),
            ("name_boundary", T + ".v1~acme.package._.instance_extra.v1", OUT),
            ("type_kind", T + ".v1~" + I + ".v1~", OUT),
            ("longer_chain", T + ".v1~" + I + ".v1~acme.package._.item.v1", OUT),
        ],
    ),
    # README §10: with both minors pinned, only that exact identifier.
    *_table(
        "instance_pinned",
        [("", T + ".v1.0~" + I + ".v1.0")],
        [
            ("self", T + ".v1.0~" + I + ".v1.0", IN),
            ("type_minor_omitted", T + ".v1~" + I + ".v1.0", OUT),
            ("instance_minor_omitted", T + ".v1.0~" + I + ".v1", OUT),
            ("type_minor_differs", T + ".v1.1~" + I + ".v1.0", OUT),
            ("instance_minor_differs", T + ".v1.0~" + I + ".v1.1", OUT),
        ],
    ),
    # Three segments: minors are flexible or pinned independently per segment.
    *_table(
        "chain_instance",
        [("", INSTANCE)],
        [
            ("self", INSTANCE, IN),
            ("instance_minor", INSTANCE + ".0", IN),
            (
                "base_minor",
                "gts.x.core.resources.resource.v1.0~"
                "acme.storage.resources.bucket.v1~acme.prod._.uploads.v1",
                IN,
            ),
            (
                "derived_minor",
                RESOURCE + "acme.storage.resources.bucket.v1.2~acme.prod._.uploads.v1",
                IN,
            ),
            (
                "all_minors",
                "gts.x.core.resources.resource.v1.2~"
                "acme.storage.resources.bucket.v1.3~acme.prod._.uploads.v1.4",
                IN,
            ),
            ("instance_major_digit_boundary", INSTANCE + "0", OUT),
            (
                "derived_major_digit_boundary",
                RESOURCE + "acme.storage.resources.bucket.v12~acme.prod._.uploads.v1",
                OUT,
            ),
            (
                "base_major_digit_boundary",
                "gts.x.core.resources.resource.v12~"
                "acme.storage.resources.bucket.v1~acme.prod._.uploads.v1",
                OUT,
            ),
            ("type_kind", INSTANCE + "~", OUT),
            ("parent_type", BUCKET, OUT),
        ],
    ),
    *_table(
        "chain_instance_pinned_instance",
        [("", INSTANCE + ".0")],
        [
            ("self", INSTANCE + ".0", IN),
            (
                "flexible_types",
                "gts.x.core.resources.resource.v1.5~"
                "acme.storage.resources.bucket.v1.6~acme.prod._.uploads.v1.0",
                IN,
            ),
            ("omitted_minor", INSTANCE, OUT),
            ("other_minor", INSTANCE + ".1", OUT),
        ],
    ),
    *_table(
        "chain_instance_pinned_derived",
        [("", RESOURCE + "acme.storage.resources.bucket.v1.0~acme.prod._.uploads.v1")],
        [
            (
                "self",
                RESOURCE + "acme.storage.resources.bucket.v1.0~acme.prod._.uploads.v1",
                IN,
            ),
            (
                "flexible_others",
                "gts.x.core.resources.resource.v1.7~"
                "acme.storage.resources.bucket.v1.0~acme.prod._.uploads.v1.7",
                IN,
            ),
            ("omitted_minor", INSTANCE, OUT),
            (
                "other_minor",
                RESOURCE + "acme.storage.resources.bucket.v1.1~acme.prod._.uploads.v1",
                OUT,
            ),
        ],
    ),
    *_table(
        "chain_instance_pinned_base",
        [
            (
                "",
                "gts.x.core.resources.resource.v1.0~"
                "acme.storage.resources.bucket.v1~acme.prod._.uploads.v1",
            )
        ],
        [
            (
                "self",
                "gts.x.core.resources.resource.v1.0~"
                "acme.storage.resources.bucket.v1~acme.prod._.uploads.v1",
                IN,
            ),
            (
                "flexible_others",
                "gts.x.core.resources.resource.v1.0~"
                "acme.storage.resources.bucket.v1.3~acme.prod._.uploads.v1.4",
                IN,
            ),
            ("omitted_minor", INSTANCE, OUT),
            (
                "other_minor",
                "gts.x.core.resources.resource.v1.1~"
                "acme.storage.resources.bucket.v1~acme.prod._.uploads.v1",
                OUT,
            ),
        ],
    ),
    # README §10 "Minor and chain wildcards in a later segment".
    *_table(
        "later_minor_wildcard",
        [("", T + ".v1~" + I + ".v1.*")],
        [
            ("instance_omitted_minor", T + ".v1~" + I + ".v1", OUT),
            ("instance_explicit_minor", T + ".v1~" + I + ".v1.0", IN),
            ("type_omitted_minor", T + ".v1~" + I + ".v1~", OUT),
            ("type_explicit_minor", T + ".v1.2~" + I + ".v1.0~", IN),
            ("descendant", T + ".v1~" + I + ".v1.0~acme.package._.item.v2", IN),
        ],
    ),
    *_table(
        "later_chain_wildcard",
        [("", T + ".v1~" + I + ".v1~*")],
        [
            ("instance_omitted_minor", T + ".v1~" + I + ".v1", OUT),
            ("instance_explicit_minor", T + ".v1~" + I + ".v1.0", OUT),
            ("type_omitted_minor", T + ".v1~" + I + ".v1~", IN),
            ("type_explicit_minor", T + ".v1.2~" + I + ".v1.0~", IN),
            ("descendant", T + ".v1~" + I + ".v1.0~acme.package._.item.v2", IN),
        ],
    ),
    # README §10 "UUID tails and prefix boundaries".
    *_table(
        "uuid",
        [("", T + ".v1~" + UUID)],
        [
            ("self", T + ".v1~" + UUID, IN),
            ("type_minor", T + ".v1.2~" + UUID, IN),
            ("other_uuid", T + ".v1~" + OTHER_UUID, OUT),
            ("other_type_major", T + ".v2~" + UUID, OUT),
            ("type_major_digit_boundary", T + ".v12~" + UUID, OUT),
        ],
    ),
    *_table(
        "uuid_pinned",
        [("", T + ".v1.0~" + UUID)],
        [
            ("self", T + ".v1.0~" + UUID, IN),
            ("omitted_minor", T + ".v1~" + UUID, OUT),
            ("other_minor", T + ".v1.1~" + UUID, OUT),
        ],
    ),
    *_table(
        "derived_uuid",
        [("", T + ".v1~acme.package._.derived.v1~" + UUID)],
        [
            ("both_minors", T + ".v1.1~acme.package._.derived.v1.2~" + UUID, IN),
            ("other_uuid", T + ".v1~acme.package._.derived.v1~" + OTHER_UUID, OUT),
            ("base_uuid", T + ".v1~" + UUID, OUT),
            (
                "derived_major_digit_boundary",
                T + ".v1~acme.package._.derived.v12~" + UUID,
                OUT,
            ),
        ],
    ),
    *_table(
        "derived_uuid_pinned",
        [("", T + ".v1~acme.package._.derived.v1.0~" + UUID)],
        [
            ("self", T + ".v1.4~acme.package._.derived.v1.0~" + UUID, IN),
            ("omitted_minor", T + ".v1~acme.package._.derived.v1~" + UUID, OUT),
            ("other_minor", T + ".v1~acme.package._.derived.v1.1~" + UUID, OUT),
        ],
    ),
    *_table(
        "universal",
        [("", "gts.*")],
        [
            ("type", T + ".v1~", IN),
            ("instance", T + ".v1~" + I + ".v1", IN),
            ("uuid_instance", T + ".v1~" + UUID, IN),
            ("length_1024", VENDOR_WITNESS, IN),
        ],
    ),
    # A token prefix is anchored to the first segment, on token boundaries.
    *_table(
        "vendor_prefix",
        [("", "gts.vendor.*")],
        [
            ("type", T + ".v1.0~", IN),
            ("other_package", "gts.vendor.other.namespace.type.v1~", IN),
            ("token_boundary", "gts.vendor_extra.package.namespace.type.v1~", OUT),
            (
                "token_boundary_instance",
                "gts.vendor_extra.package.namespace.type.v1~" + I + ".v1",
                OUT,
            ),
        ],
    ),
    *_table(
        "acme_prefix",
        [("", "gts.acme.*")],
        [
            ("vendor_in_later_segment", T + ".v1~" + I + ".v1", OUT),
            (
                "vendor_in_later_type_segment",
                T + ".v1~acme.package._.derived.v1~",
                OUT,
            ),
        ],
    ),
    *_table(
        "package_prefix",
        [("", "gts.vendor.package.*")],
        [
            ("instance", T + ".v1~" + I + ".v1", IN),
            ("other_package", "gts.vendor.other.namespace.type.v1~", OUT),
        ],
    ),
    *_table(
        "namespace_prefix",
        [("", "gts.vendor.package.namespace.*")],
        [
            ("other_type", "gts.vendor.package.namespace.other.v1~", IN),
            ("other_namespace", "gts.vendor.package.other.type.v1~", OUT),
        ],
    ),
    # README §10: a named suffix requires another segment; unlike `~*`, it
    # cannot be empty.
    *_table(
        "chain_vendor_prefix",
        [("", T + ".v1~acme.*")],
        [
            ("instance", T + ".v1.0~" + I + ".v1", IN),
            ("derived_type", T + ".v1~acme.package._.derived.v1~", IN),
            ("base_itself", T + ".v1.0~", OUT),
            ("other_vendor", T + ".v1~other.package._.instance.v1", OUT),
        ],
    ),
    *_table(
        "chain_namespace_prefix",
        [("", T + ".v1~acme.package._.*")],
        [
            ("instance", T + ".v1.5~" + I + ".v1", IN),
            ("other_namespace", T + ".v1~acme.package.other.instance.v1", OUT),
        ],
    ),
    *_table(
        "chain_prefix_other_base_major",
        [("", T + ".v2~acme.*")],
        [("instance", T + ".v1~" + I + ".v1.3", OUT)],
    ),
    # Explicit-minor wildcards in later type segments of the §9.6.2 example.
    *_table(
        "derived_minor_wildcard",
        [("", RESOURCE + "acme.storage.resources.bucket.v1.*")],
        [
            ("explicit_minor", RESOURCE + "acme.storage.resources.bucket.v1.2~", IN),
            ("omitted_minor", BUCKET, OUT),
            ("instance", RESOURCE + "acme.storage.resources.bucket.v1.0", IN),
        ],
    ),
    *_table(
        "instance_minor_wildcard",
        [("", BUCKET + "acme.prod._.uploads.v1.*")],
        [("omitted_minor", INSTANCE, OUT), ("explicit_minor", INSTANCE + ".3", IN)],
    ),
    *_table(
        "family",
        [("", FAMILY)],
        [
            ("type", RESOURCE, IN),
            ("instance", INSTANCE, IN),
            ("other_type", "gts.x.core.resources.other.v1~", OUT),
            ("other_namespace", "gts.x.core.events.event.v1~", OUT),
        ],
    ),
    *_table(
        "type_derived_and_uuid",
        [("", RESOURCE)],
        [
            ("instance", INSTANCE, IN),
            ("uuid_instance", ANONYMOUS, IN),
            ("derived_minor", RESOURCE + "acme.storage.resources.bucket.v1.2~", IN),
            ("vendor_in_later_segment", "gts.acme.storage.resources.bucket.v1~", OUT),
        ],
    ),
    *_table(
        "derived_type",
        [("", BUCKET)],
        [
            (
                "earlier_minor",
                "gts.x.core.resources.resource.v1.2~acme.storage.resources.bucket.v1~",
                IN,
            ),
            ("explicit_minor", RESOURCE + "acme.storage.resources.bucket.v1.2~", IN),
            ("base", RESOURCE, OUT),
            ("instance_beside", RESOURCE + "acme.storage.resources.bucket.v1.0", OUT),
        ],
    ),
    *_table(
        "anchored_type",
        [("", "gts.acme.storage.resources.bucket.v1~")],
        [("later_segment", BUCKET, OUT)],
    ),
    # Unsigned 32-bit versions and the 1024-character limit.
    *_table(
        "max_major",
        [("", "gts.x.core.resources.resource.v" + MAX_VERSION + "~")],
        [
            ("self", "gts.x.core.resources.resource.v" + MAX_VERSION + "~", IN),
            (
                "previous_major",
                "gts.x.core.resources.resource.v" + PREVIOUS_VERSION + "~",
                OUT,
            ),
        ],
    ),
    *_table(
        "max_minor",
        [("", RESOURCE)],
        [("max_minor", "gts.x.core.resources.resource.v1." + MAX_VERSION + "~", IN)],
    ),
    *_table("length_limit_vendor", [("", VENDOR_PATTERN)], [("witness", VENDOR_WITNESS, IN)]),
    *_table(
        "length_limit_version_marker",
        [("", VERSION_PATTERN)],
        [("witness", VERSION_WITNESS, IN)],
    ),
    *_table(
        "minor_boundary",
        [("", MINOR_BOUNDARY_WILDCARD)],
        [
            ("explicit_minor", MINOR_BOUNDARY_INSTANCE + ".0", IN),
            ("omitted_minor", MINOR_BOUNDARY_INSTANCE, OUT),
        ],
    ),
    *_table(
        "empty_selection",
        [("", LONGEST_PATTERN)],
        [("type", RESOURCE, OUT)],
    ),
    # Former OP#4 vectors.
    *_table(
        "op4_chain_vendor",
        [("", "gts.x.test4.events.type.v1~abc.*")],
        [
            ("instance", "gts.x.test4.events.type.v1~abc.app._.custom_event.v1.2", IN),
            ("derived_type", "gts.x.test4.events.type.v1~abc.app._.custom.v1~", IN),
        ],
    ),
)


COVERAGE_CASES = (
    # README §10 "Pattern coverage examples".
    pytest.param(T + ".v1~", T + ".v1~*", True, None, id="type_covers_chain_wildcard"),
    pytest.param(T + ".v1~", T + ".v1.*", True, None, id="type_covers_minor_wildcard"),
    pytest.param(
        T + ".v1.*", T + ".v1~*", False, T + ".v1~",
        id="minor_wildcard_excludes_omitted_minor",
    ),
    pytest.param(
        T + ".v1.*", T + ".v1.0~*", True, None, id="minor_wildcard_covers_pinned_chain"
    ),
    pytest.param(
        T + ".v1~" + I + ".v1",
        T + ".v1~" + I + ".v1.*",
        False,
        T + ".v1~" + I + ".v1.0~",
        id="instance_excludes_minor_wildcard",
    ),
    # Equal and narrower selectors.
    pytest.param(FAMILY, FAMILY, True, None, id="equal_wildcards"),
    pytest.param(LONGEST_PATTERN, LONGEST_PATTERN, True, None, id="equal_length_1024"),
    pytest.param(FAMILY, BUCKET_FAMILY, True, None, id="family_covers_derived_family"),
    pytest.param(RESOURCE, RESOURCE + "*", True, None, id="type_covers_own_chain"),
    pytest.param(RESOURCE, BUCKET_FAMILY, True, None, id="type_covers_derived_family"),
    pytest.param(
        RESOURCE + "acme.*", BUCKET_FAMILY, True, None, id="chain_vendor_covers_family"
    ),
    pytest.param(
        FAMILY, "gts.x.core.resources.resource.v*", True, None,
        id="type_family_covers_version_marker",
    ),
    pytest.param(
        "gts.x.core.resources.resource.v*", FAMILY, True, None,
        id="version_marker_covers_type_family",
    ),
    pytest.param("gts.vendor.*", "gts.vendor.pkg.*", True, None, id="vendor_covers_package"),
    pytest.param(
        "gts.x.a.b.c.v1~",
        "gts.x.a.b.c.v1~acme.prod._.uploads.v2.*",
        True,
        None,
        id="type_covers_later_minor_wildcard",
    ),
    pytest.param(
        "gts.a.b.c.d.v1~*", "gts.a.b.c.d.v1.0~a.b.*", True, None,
        id="chain_covers_explicit_minor_prefix",
    ),
    pytest.param(
        "gts.a.b.c.d.v1~", "gts.a.b.c.d.v1.0~a.b.*", True, None,
        id="type_covers_explicit_minor_prefix",
    ),
    pytest.param(
        "gts.a.b.c.d.v1.1~", "gts.a.b.c.d.v1.1~a.b.*", True, None,
        id="pinned_type_covers_same_minor_prefix",
    ),
    # Selectors that select nothing are covered by any filter.
    pytest.param(FAMILY, LONGEST_PATTERN, True, None, id="empty_longest"),
    pytest.param(FAMILY, EMPTY_VENDOR_PATTERN, True, None, id="empty_vendor"),
    pytest.param(FAMILY, EMPTY_VERSION_PATTERN, True, None, id="empty_version_marker"),
    pytest.param(
        EMPTY_VENDOR_PATTERN, "gts." + "a" * 1012 + ".*", True, None,
        id="empty_filter_covers_empty_candidate",
    ),
    pytest.param(
        MINOR_BOUNDARY_INSTANCE, MINOR_BOUNDARY_WILDCARD, True, None,
        id="length_limited_minor_wildcard_selects_only_instances",
    ),
    # Broader or different selectors; the witness shows the difference.
    pytest.param(
        "gts.x.core.resources.resource.v1.*", RESOURCE + "*", False, RESOURCE,
        id="minor_wildcard_excludes_flexible_chain",
    ),
    pytest.param(
        RESOURCE, FAMILY, False, "gts.x.core.resources.resource.v2~",
        id="type_excludes_other_majors",
    ),
    pytest.param(
        FAMILY, "gts.x.core.resources.*", False, "gts.x.core.resources.other.v1~",
        id="family_excludes_namespace",
    ),
    pytest.param(FAMILY, OTHER, False, "gts.x.core.events.event.v1~", id="other_family"),
    pytest.param(
        FAMILY,
        "gts.x.core.resources.resource_extra.*",
        False,
        "gts.x.core.resources.resource_extra.v1~",
        id="type_token_boundary",
    ),
    pytest.param(
        BUCKET,
        RESOURCE + "acme.storage.resources.bucket.v1.*",
        False,
        RESOURCE + "acme.storage.resources.bucket.v1.0",
        id="derived_type_excludes_instance_beside",
    ),
    pytest.param(
        BUCKET + "*",
        RESOURCE + "acme.storage.resources.bucket.v1.*",
        False,
        RESOURCE + "acme.storage.resources.bucket.v1.0",
        id="later_chain_wildcard_excludes_instance",
    ),
    pytest.param(
        INSTANCE, BUCKET + "acme.prod._.uploads.*", False, INSTANCE + "0",
        id="instance_excludes_wildcard",
    ),
    pytest.param(
        "gts.x.core.resources.resource.v1.2~acme.*",
        RESOURCE + "acme.*",
        False,
        "gts.x.core.resources.resource.v1.3~acme.x._.y.v1~",
        id="explicit_first_minor_before_wildcard",
    ),
    pytest.param(
        "gts.x.a.b.c.v1~acme.prod._.uploads.v2",
        "gts.x.a.b.c.v1~acme.prod._.uploads.v2.*",
        False,
        "gts.x.a.b.c.v1~acme.prod._.uploads.v2.0~",
        id="instance_excludes_types_of_minor_wildcard",
    ),
    pytest.param(
        "gts.a.b.c.d.v1.1~*", "gts.a.b.c.d.v1~a.b.c.d.*", False,
        "gts.a.b.c.d.v1~a.b.c.d.v1", id="pinned_chain_excludes_omitted_minor",
    ),
    pytest.param(
        "gts.a.b.c.d.v1.1~*", "gts.a.b.c.d.v1.0~a.b.c.d.*", False,
        "gts.a.b.c.d.v1.0~a.b.c.d.v1", id="pinned_chain_excludes_other_minor",
    ),
    pytest.param(
        MINOR_BOUNDARY_INSTANCE + ".0", MINOR_BOUNDARY_WILDCARD, False,
        MINOR_BOUNDARY_INSTANCE + ".1",
        id="explicit_minor_excludes_length_limited_wildcard",
    ),
    # The neighbours of the empty-selection boundary select a 1024-character ID.
    pytest.param(FAMILY, VENDOR_PATTERN, False, VENDOR_WITNESS, id="nonempty_vendor"),
    pytest.param(
        FAMILY, VERSION_PATTERN, False, VERSION_WITNESS, id="nonempty_version_marker"
    ),
)


VALID_PATTERNS = (
    pytest.param("gts.*", id="any"),
    pytest.param("gts.x.*", id="vendor"),
    pytest.param("gts.x.core.*", id="package"),
    pytest.param("gts.x.core.events.*", id="namespace"),
    pytest.param("gts.x.core.events.type.*", id="type"),
    pytest.param("gts.x.core.events.type.v*", id="version_marker"),
    pytest.param("gts.x.core.events.type.v1.*", id="major"),
    pytest.param("gts.x.core.events.type.v0.*", id="major_zero"),
    pytest.param("gts.x.core.events.type.v1~*", id="chain"),
    pytest.param("gts.x.core.events.type.v1.0~*", id="chain_minor"),
    pytest.param("gts.x.core.events.type.v1~xyz.*", id="chain_vendor"),
    pytest.param("gts.x.core.events.type.v1~x.y._.w.v1.*", id="chain_major"),
    pytest.param(
        "gts.x.core.events.type.v1~x.core._.audit_event.v1~xyz.app.*",
        id="chain_two_types",
    ),
    pytest.param("gts.x.core.events.type.v1~", id="concrete_type"),
    pytest.param("gts.x.core.events.type.v1.2~", id="concrete_type_minor"),
    pytest.param(
        "gts.x.core.events.type.v1~ven.app._.custom_event.v1~",
        id="concrete_chained_type",
    ),
    pytest.param(
        "gts.x.core.events.topic.v1~ven.app._.custom_event_topic.v1.2",
        id="concrete_well_known_instance",
    ),
    pytest.param("gts.x.core.events.type.v1~" + UUID, id="concrete_anonymous_instance"),
    pytest.param("gts.nobody.unregistered.*", id="unregistered_prefix"),
    pytest.param(LONGEST_PATTERN, id="length_1024"),
    pytest.param(VENDOR_WITNESS, id="concrete_length_1024"),
    pytest.param("gts.x.core.resources.resource.v" + MAX_VERSION + "~", id="large_major"),
    pytest.param("gts.x.core.resources.resource.v1." + MAX_VERSION + "~", id="large_minor"),
    pytest.param(
        "gts.x.core.resources.resource.v" + MAX_VERSION + ".*",
        id="large_major_wildcard",
    ),
)

INVALID_PATTERNS = (
    # README §10 "Invalid pattern examples".
    pytest.param("gts.vendor.package.namespace.typ*", id="partial_type"),
    pytest.param(T + ".v1*", id="partial_major"),
    pytest.param(T + ".v1.0.*", id="after_minor"),
    pytest.param(T + ".v*~*", id="two_wildcards_version"),
    pytest.param("gts.vendor.*.namespace.type.v1~", id="wildcard_in_middle"),
    pytest.param(T + ".v" + OVERFLOW_VERSION + "~*", id="chain_major_overflow"),
    # Version bounds.
    pytest.param("gts.x.core.events.type.v" + OVERFLOW_VERSION + "~", id="major_overflow"),
    pytest.param(
        "gts.x.core.events.type.v1." + OVERFLOW_VERSION + "~", id="minor_overflow"
    ),
    pytest.param(
        "gts.x.core.events.type.v" + OVERFLOW_VERSION + ".*",
        id="wildcard_major_overflow",
    ),
    pytest.param(
        "gts.x.core.events.type.v1~acme.prod._.uploads.v" + OVERFLOW_VERSION,
        id="instance_major_overflow",
    ),
    pytest.param(
        "gts.x.core.events.type.v1~acme.prod._.uploads.v1." + OVERFLOW_VERSION,
        id="instance_minor_overflow",
    ),
    pytest.param(
        "gts.x.core.events.type.v1~acme.prod._.uploads.v" + OVERFLOW_VERSION + ".*",
        id="later_wildcard_major_overflow",
    ),
    # Wildcard placement.
    pytest.param("", id="empty"),
    pytest.param("*", id="bare_wildcard"),
    pytest.param("gts", id="prefix_without_dot"),
    pytest.param("x.core.events.type.v1~", id="missing_prefix"),
    pytest.param("gts.", id="prefix_only"),
    pytest.param("gts*", id="wildcard_in_prefix"),
    pytest.param("gts.vendor*", id="partial_vendor"),
    pytest.param("gts.x.core.events.type.v1.0*", id="partial_minor"),
    pytest.param("gts.x.core.events.type.v1~abc*", id="partial_chain_vendor"),
    pytest.param("gts.x.test4.events.type.v1*abc", id="wildcard_inside_token"),
    pytest.param("gts.*.pkg.ns.*", id="vendor_and_namespace_wildcards"),
    pytest.param("gts.x.core.*~*", id="two_wildcards"),
    pytest.param("gts.x.core.events.type.v1~**", id="double_wildcard"),
    pytest.param("gts.x.core.events.type.v1~*~", id="wildcard_not_last"),
    pytest.param("gts.x.core.events.type.v1~x.y._.w.v1@name", id="attribute"),
    pytest.param('gts.x.core.events.type.v1~[name="x"]', id="query"),
    # UUID tails.
    pytest.param("gts.x.core.events.type.v1~550e8400-*", id="partial_uuid"),
    pytest.param("gts.x.core.events.type.v1~" + UUID + "*", id="wildcard_after_uuid"),
    pytest.param("gts.x.core.events.type.v1~" + UUID + "~", id="tilde_after_uuid"),
    pytest.param("gts.x.core.events.type.v1~" + UUID + "~*", id="chain_after_uuid"),
    pytest.param("gts.x.core.events.type.v1~" + UUID.upper(), id="uppercase_uuid"),
    # Spelling.
    pytest.param("GTS.x.core.*", id="uppercase_prefix"),
    pytest.param("gts.X.core.*", id="uppercase_token"),
    pytest.param(" gts.x.core.*", id="leading_space"),
    pytest.param("gts.x.core.* ", id="trailing_space"),
    pytest.param("gts.x.core.events.type.v1~\n", id="trailing_lf"),
    pytest.param("gts.x.core.events.type.v1~\r", id="trailing_cr"),
    pytest.param("gts.x.core.events.type.v1~ ", id="trailing_unicode_separator"),
    pytest.param("gts.x. core.*", id="inner_space"),
    pytest.param("gts://gts.x.core.events.type.v1~", id="uri_form"),
    pytest.param("gts://gts.*", id="uri_form_wildcard"),
    pytest.param("gts.x.core-1.events.*", id="hyphen"),
    pytest.param("gts.vendor.pkg.ns.type.v1~a-b.*", id="chain_hyphen"),
    pytest.param("gts.1x.core.*", id="token_starts_with_digit"),
    pytest.param("gts.x.сore.*", id="non_ascii"),
    # Identifier structure.
    pytest.param("gts.x.core.events.type.v1", id="single_segment_instance"),
    pytest.param("gts.x.test4.events.type", id="missing_version"),
    pytest.param("gts.x.core.events.type~", id="missing_version_type"),
    pytest.param("gts.a.b.c.d~a.b.c.d.*", id="missing_version_before_chain"),
    pytest.param("gts.x.test4.events.type.v1~abc", id="incomplete_segment"),
    pytest.param("gts.x.core.events.type.vx.*", id="bad_major"),
    pytest.param("gts.x.core.events.type.v01~", id="major_leading_zero"),
    pytest.param("gts.x.core.events.type.v1.01~*", id="minor_leading_zero"),
    pytest.param("gts.x.core.events.type.v1~~", id="double_tilde"),
    # Length.
    pytest.param("gts." + "a" * 1019 + ".*", id="length_1025"),
    pytest.param(EMPTY_VENDOR_COMPLETION, id="concrete_length_1025"),
)
