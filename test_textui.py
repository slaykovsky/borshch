from core import initial_state, render, key as rusty_key
from textui import step, parse, dispatch, mainloop
from pytest import raises
from effect import Func, raise_
from effect.testing import noop, perform_sequence
from effect.io import Display, Prompt

from storage import SaveGame

in_street = initial_state.set(location_name="Street")


def test_parse():
    assert parse("move up") == ["move", "up"]
    assert parse("move in there") == ["move", "in there"]
    assert parse("take bottle") == ["take", "bottle"]
    assert parse("take rusty key") == ["take", "rusty key"]


def test_parse_error():
    with raises(Exception) as err_info:
        parse("move")
    assert str(
        err_info.value
    ) == "Expected: `take <item>` or `move <direction>`"


def test_dispatch():
    with_key = in_street.transform(
        ["inventory"], [rusty_key],
        ["world", "Street", "items"], {}
    )
    assert dispatch(initial_state, "move", "east") == in_street
    assert dispatch(in_street, "take", "rusty key") == with_key


def test_dispatch_error():
    with raises(Exception) as err_info:
        dispatch(initial_state, "move", "up")
    assert str(
        err_info.value
    ) == "Invalid argument!"


def test_step():
    expected_effects = [
        (Display(render(initial_state)), noop),
        (Prompt("> "), lambda i: "move east"),
        (Display("Okay."), noop)
    ]
    eff = step(initial_state)
    result = perform_sequence(expected_effects, eff)
    assert result == in_street


def test_step_bad_command():
    expected_effects = [
        (Display(render(initial_state)), noop),
        (Prompt("> "), lambda i: "do a flip"),
        (Display("Expected: `take <item>` or `move <direction>`"), noop)
    ]
    eff = step(initial_state)
    result = perform_sequence(expected_effects, eff)
    assert result == initial_state


def test_quit_game():
    for exc in (KeyboardInterrupt(), EOFError()):
        expected_effects = [
            (Display(render(initial_state)), noop),
            (Prompt("> "), lambda i: raise_(exc)),
            (Display("\nThanks for playing!"), noop),
        ]
        eff = step(initial_state)
        with raises(SystemExit):
            perform_sequence(expected_effects, eff)


def test_mainloop():
    expected_effects = [
        (Display(render(initial_state)), noop),
        (Prompt("> "), lambda i: "move east"),
        (Display("Okay."), noop),
        (SaveGame(state=in_street), noop),
        (Display(render(in_street)), noop),
        (Prompt("> "), lambda i: raise_(KeyboardInterrupt())),
        (Display("\nThanks for playing!"), noop)
    ]
    eff = mainloop(initial_state)

    with raises(SystemExit):
        perform_sequence(expected_effects, eff)
