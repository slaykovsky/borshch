from pyrsistent import pmap
from core import Thing, Location, GameState, take, move


key = Thing(name="rusty key")
home = Location(
    name="Home",
    description="Home is where the heart is!",
    exits={
        "east": (None, "Street"),
        "down": (key, "Basement")
    }
)
street = Location(
    name="Street",
    description="The street next to your house.",
    exits={"west": (None, "Home")},
    items={key.name: key}
)
basement = Location(
    name="Basement",
    description="You found the basement!",
    exits={"up": (None, "Home")}
)
world = pmap({x.name: x for x in [home, street, basement]})
initial_state = GameState(location_name="Home", world=world)
in_street = initial_state.set(location_name="Street")
in_street_with_key = in_street.transform(
    ["world", "Street", "items"], lambda _: {},
    ["inventory"], lambda _: [key]
)


def test_take_not_found():
    assert take(initial_state, "some item") is None


def test_take_something():
    in_street = initial_state.set(location_name="Street")
    assert take(in_street, "rusty key") == in_street_with_key


def test_move_invalid():
    assert move(initial_state, "inward") is None


def test_move_without_key():
    assert move(initial_state, "down") is None


def test_move():
    assert move(initial_state, "east") == in_street


def test_move_with_key():
    in_home_with_key = in_street_with_key.set(location_name="Home")
    expected_state = in_home_with_key.set(location_name="Basement")
    assert move(in_home_with_key, "down") == expected_state
