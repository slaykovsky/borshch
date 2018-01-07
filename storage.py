import json
from functools import partial

from pyrsistent import thaw, PClass, field
from sqlite3 import connect
from core import Thing, Location, GameState, initial_state
from effect import sync_performer, TypeDispatcher


class SaveGame(PClass):
    state = field()

class LoadGame(PClass):
    pass


CREATE_LOCATION = (
    "CREATE TABLE IF NOT EXISTS location (name text primary key, description text,"
    "exits blob, items blob)"
)
CREATE_STATE = "CREATE TABLE IF NOT EXISTS state (location_name text, inventory blob)"
INSERT_LOCATION = (
    "INSERT OR REPLACE INTO location (name, description, exits, items) "
    "VALUES (?, ?, ?, ?)"
)
INSERT_STATE = "INSERT INTO state (location_name, inventory) VALUES (?, ?)"
DELETE_STATE = "DELETE FROM state"
SELECT_LOCATION = "SELECT name, description, exits, items FROM location"
SELECT_STATE = "SELECT location_name, inventory FROM state"
FILENAME = "/tmp/textgamestate.sqlite3"


def connect_db():
    return connect(FILENAME)


def initialize(conn, initial=None):
    curs = conn.cursor()
    setup(curs)
    st = load_state(curs)
    if st is None:
        save_state(curs, initial)
        st = initial
    return load_state(curs)


def setup(cursor):
    cursor.execute(CREATE_LOCATION)
    cursor.execute(CREATE_STATE)


def serialize_state(state):
    return (
        state.location_name,
        json.dumps([x.name for x in state.inventory])
    )


def serialize_world(world):
    return map(serialize_location, world.values())


def serialize_exits(exits):
    return json.dumps([
        [direction, key.name if key is not None else None, destination]
        for direction, (key, destination) in exits.items()
    ])


def serialize_location(loc):
    items = json.dumps(thaw(loc.items.keys()))
    exits = serialize_exits(loc.exits)
    return loc.name, loc.description, exits, items


def save_state(cursor, state):
    cursor.execute(DELETE_STATE)
    cursor.execute(INSERT_STATE, serialize_state(state))
    for params in serialize_world(state.world):
        cursor.execute(INSERT_LOCATION, params)


@sync_performer
def perform_save_game_sqlite(conn, dispatcher, save_game):
    save_state(conn.cursor(), save_game.state)
    conn.commit()


@sync_performer
def perform_load_game_sqlite(conn, disp, load_game):
    return initialize(conn)


def sqlite_dispatcher(conn):
    return TypeDispatcher({
        SaveGame: partial(perform_save_game_sqlite, conn),
        LoadGame: partial(perform_load_game_sqlite, conn)
    })


def save_location(cursor, loc):
    items = json.dumps(thaw(loc.items.keys()))
    exits = serialize_exits(loc.exits)
    cursor.execute(
        INSERT_LOCATION,
        (loc.name, loc.description, exits, items)
    )


def load_location(row):
    exits = {
        direction: (
            Thing(name=key_name) if key_name is not None else None,
            dest
        ) for direction, key_name, dest in json.loads(row[2])
    }
    items = {x: Thing(name=x) for x in json.loads(row[3])}
    return Location(
        name=row[0],
        description=row[1],
        exits=exits,
        items=items
    )


def load_world(rows):
    return {row[0]: load_location(row) for row in rows}


def load_game_state(state_row, world):
    return GameState(
        world=world,
        location_name=state_row[0],
        inventory=[Thing(name=x) for x in json.loads(state_row[1])]
    )


def load_state(cursor):
    world = load_world(cursor.execute(SELECT_LOCATION))
    state_rows = list(cursor.execute(SELECT_STATE))
    if len(state_rows) == 1:
        return load_game_state(state_rows[0], world)
