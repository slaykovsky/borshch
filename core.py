from functools import reduce
from pyrsistent import PClass, pmap_field, field, pmap, pvector_field
from toolz.functoolz import thread_first


ROOM_FORMAT = """
* {name} *
{description}

Exits:
{exits}

Items here: {items}

Your inventory: {inventory}
"""


class Thing(PClass):
    name = field(str)


class Location(PClass):
    name = field(str)
    description = field(str)
    exits = pmap_field(str, tuple)
    items = pmap_field(str, Thing)


class GameState(PClass):
    location_name = field(str)
    world = pmap_field(str, Location)
    inventory = pvector_field(Thing)

    @property
    def location(self):
        return self.world[self.location_name]


def move(state, exit_name):
    if exit_name not in state.location.exits:
        return None

    key, location_name = state.location.exits.get(exit_name)
    if key is not None and key not in state.inventory:
        return None
    return state.set(location_name=location_name)


def multimove(state, directions):
    return reduce(move, directions, state)


def take(state, item_name):
    item = state.location.items.get(item_name)
    if item is None: return None
    return state.transform(
        ["world", state.location.name, "items"], lambda items:
        items.remove(item_name),
        ["inventory"], lambda inv: inv.append(item)
    )


def render(state):
    def render_exit(exit_name, key, destination):
        desc = "* {} to {}".format(exit_name, destination)
        return desc + (" (locked)" if key is not None else "")

    exits = "\n".join(
        render_exit(direction, key, destination)
        for direction, (key, destination) in state.location.exits.items()
    )
    items = ", ".join(state.location.items.keys())
    inventory = ", ".join(item.name for item in state.inventory)
    return ROOM_FORMAT.format(
        name=state.location.name,
        description=state.location.description,
        exits=exits,
        items=items,
        inventory=inventory
    )



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
