from fpflask import FunctionalFlask
from flask import render_template, redirect, url_for
from effect import Effect, base_dispatcher, ComposedDispatcher
from effect.do import do, do_return


from core import initial_state, move, take
from storage import (
    SaveGame, LoadGame,
    sqlite_dispatcher, connect_db, initialize
)


app = FunctionalFlask("BORSHCH")


@app.route("/")
def root(request):
    return Effect(LoadGame()).on(
        lambda st: render_template("game.html", state=st)
    )


@app.route("/move", methods=["POST"])
@do
def handle_move(request):
    exit_name = request.form["exit_name"]
    state = yield Effect(LoadGame())
    st = move(state, exit_name)
    if st is not None:
        yield Effect(SaveGame(state=st))
    yield do_return(redirect(url_for("root")))


@app.route("/take", methods=["POST"])
@do
def handle_take(request):
    item_name= request.form["item_name"]
    state = yield Effect(LoadGame())
    st = take(state, item_name)
    if st is not None:
        yield Effect(SaveGame(state=st))
    yield do_return(redirect(url_for("root")))


if __name__ == "__main__":
    conn = connect_db()
    initialize(conn, initial_state)
    dispatcher = ComposedDispatcher([base_dispatcher, sqlite_dispatcher(conn)])
    app.flask.config.update(PROPAGATE_EXCEPTIONS=True)
    app.run(dispatcher)
