"""Regression tests for scoped Shift+Enter VT100 remapping."""

from __future__ import annotations

from prompt_toolkit.input.vt100_parser import (
    ANSI_SEQUENCES,
    Vt100Parser,
    _IS_PREFIX_OF_LONGER_MATCH_CACHE,
)
from prompt_toolkit.keys import Keys

import cli


_SHIFT_ENTER_PREFIXES = {
    sequence[:index]
    for sequence in cli._SHIFT_ENTER_SEQUENCES
    for index in range(1, len(sequence))
}


def test_temporary_vt100_sequence_mappings_restores_original_values():
    missing = object()
    original_values = {
        sequence: ANSI_SEQUENCES.get(sequence, missing)
        for sequence in cli._SHIFT_ENTER_SEQUENCES
    }
    for prefix in _SHIFT_ENTER_PREFIXES:
        _ = _IS_PREFIX_OF_LONGER_MATCH_CACHE[prefix]
    original_prefix_cache = {
        prefix: _IS_PREFIX_OF_LONGER_MATCH_CACHE.get(prefix, missing)
        for prefix in _SHIFT_ENTER_PREFIXES
    }

    with cli._temporary_vt100_sequence_mappings(
        {sequence: Keys.ControlJ for sequence in cli._SHIFT_ENTER_SEQUENCES}
    ):
        for sequence in cli._SHIFT_ENTER_SEQUENCES:
            assert ANSI_SEQUENCES[sequence] == Keys.ControlJ
        for prefix in _SHIFT_ENTER_PREFIXES:
            assert _IS_PREFIX_OF_LONGER_MATCH_CACHE.get(prefix, missing) is missing

    for sequence, original_value in original_values.items():
        if original_value is missing:
            assert sequence not in ANSI_SEQUENCES
        else:
            assert ANSI_SEQUENCES[sequence] == original_value
    restored_prefix_cache = {
        prefix: _IS_PREFIX_OF_LONGER_MATCH_CACHE.get(prefix, missing)
        for prefix in _SHIFT_ENTER_PREFIXES
    }
    assert restored_prefix_cache == original_prefix_cache


def test_shift_enter_sequences_parse_as_control_j_when_mapped():
    for sequence in cli._SHIFT_ENTER_SEQUENCES:
        parsed_keys: list[Keys | str] = []
        parser = Vt100Parser(lambda key_press: parsed_keys.append(key_press.key))

        with cli._temporary_vt100_sequence_mappings({sequence: Keys.ControlJ}):
            parser.feed_and_flush(sequence)

        assert parsed_keys == [Keys.ControlJ]


def test_temporary_vt100_sequence_mappings_restore_after_exception():
    missing = object()
    original_values = {
        sequence: ANSI_SEQUENCES.get(sequence, missing)
        for sequence in cli._SHIFT_ENTER_SEQUENCES
    }
    for prefix in _SHIFT_ENTER_PREFIXES:
        _ = _IS_PREFIX_OF_LONGER_MATCH_CACHE[prefix]
    original_prefix_cache = {
        prefix: _IS_PREFIX_OF_LONGER_MATCH_CACHE.get(prefix, missing)
        for prefix in _SHIFT_ENTER_PREFIXES
    }

    try:
        with cli._temporary_vt100_sequence_mappings(
            {sequence: Keys.ControlJ for sequence in cli._SHIFT_ENTER_SEQUENCES}
        ):
            for prefix in _SHIFT_ENTER_PREFIXES:
                assert _IS_PREFIX_OF_LONGER_MATCH_CACHE.get(prefix, missing) is missing
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    for sequence, original_value in original_values.items():
        if original_value is missing:
            assert sequence not in ANSI_SEQUENCES
        else:
            assert ANSI_SEQUENCES[sequence] == original_value
    restored_prefix_cache = {
        prefix: _IS_PREFIX_OF_LONGER_MATCH_CACHE.get(prefix, missing)
        for prefix in _SHIFT_ENTER_PREFIXES
    }
    assert restored_prefix_cache == original_prefix_cache
