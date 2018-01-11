import sys

from core import initial_state, take, move, render
from storage import connect_db, initialize
from effect import (
    ComposedDispatcher, Effect, Func,
    sync_perform, base_dispatcher
)
from effect.do import do, do_return
from effect.io import Display, Prompt, stdio_dispatcher
from storage import SaveGame, connect_db, initialize, sqlite_dispatcher


def parse(line):
    parts = line.split(" ", 1)
    if len(parts) != 2 or parts[0] not in ("take", "move"):
        raise Exception("Expected: `take <item>` or `move <direction>`")
    return parts


def dispatch(state, cmd, arg):
    handler = {"take": take, "move": move}[cmd]
    result = handler(state, arg)
    if result is None:
        raise Exception("Invalid argument!")

    return result


def display(o):
    return Effect(Display(o))


@do
def step(state):
    yield display(render(state))
    try:
        user_input = yield Effect(Prompt("> "))
        cmd, arg = parse(user_input)
        result = dispatch(state, cmd, arg)
        yield display("Okay.")
        yield do_return(result)
    except (EOFError, KeyboardInterrupt):
        yield display("\nThanks for playing!")
        sys.exit(0)
    except Exception as e:
        yield display(str(e))
        yield do_return(state)


@do
def mainloop(state):
    while True:
        state = yield step(state)
        yield Effect(SaveGame(state=state))


def startup():
    conn = connect_db()
    state = initialize(conn, initial_state)
    if state is None:
        state = initial_state
    st_dispatcher = sqlite_dispatcher(conn)
    return st_dispatcher, state


if __name__ == "__main__":
    st_dispatcher, state = startup()
    dispatcher = ComposedDispatcher([
        stdio_dispatcher,
        base_dispatcher,
        st_dispatcher
    ])
    main_eff = mainloop(state)
    sync_perform(dispatcher, main_eff)
