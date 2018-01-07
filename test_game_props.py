from functools import wraps

from hypothesis.strategies import choices
from hypothesis.stateful import RuleBasedStateMachine, rule, precondition
from toolz.functoolz import compose
from core import take, move, initial_state


def stateful(f):
    @wraps(f)
    def inner(self, *args, **kwargs):
        self.state = f(self, self.state, *args, **kwargs)
    return inner


def srulep(precond=lambda s: True, **kwargs):
    return compose(precondition(precond), rule(**kwargs), stateful)


def eligible_locked_exits(state):
    return [
        exit_name for exit_name, (req_key, dest) in
        state.location.exits.items() if req_key in state.inventory
    ]


class GameRules(RuleBasedStateMachine):
    state = initial_state

    @srulep(choice=choices())
    def move(self, state, choice):
        unlocked_exits = [
            exit_name for (exit_name, (req_key, dest)) in
            state.location.exits.items() if req_key is None
        ]
        direc = choice(unlocked_exits)
        st = move(state, direc)
        assert st.location_name == state.location.exits[direc][1]
        return st

    @srulep(
        precond=lambda self: len(self.state.location.items) > 0,
        choice=choices()
    )
    def take(self, state, choice):
        thing_name = choice(state.location.items.keys())
        st = take(state, thing_name)
        assert thing_name in (t.name for t in st.inventory)
        assert thing_name not in st.location.items
        return st

    @srulep(
        precond=lambda self: len(eligible_locked_exits(self.state)) > 0,
        choice=choices()
    )
    def move_through_locked_door(self, state, choice):
        direc = choice(eligible_locked_exits(state))
        st = move(state, direc)
        assert st.location_name == state.location.exits[direc][1]
        return st


GameRules.TestCase().runTest()
