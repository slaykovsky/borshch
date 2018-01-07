from functools import wraps
from effect import Effect, sync_perform
from flask import Flask, request


class FunctionalFlask(object):
    def __init__(self, name):
        self.flask = Flask(name)
        self.routes = []

    def route(self, *route_args, **route_kwargs):
        def decorator(f):
            self.routes.append((f, route_args, route_kwargs))
            return f
        return decorator

    def run(self, dispatcher):
        for handler, route_args, route_kwargs in self.routes:
            self._register_route(dispatcher, handler, route_args, route_kwargs)
        self.flask.run(host="0.0.0.0")

    def _register_route(self, dispatcher, handler, route_args, route_kwargs):
        @self.flask.route(*route_args, **route_kwargs)
        @wraps(handler)
        def wrapper(*args, **kwargs):
            req = request._get_current_object()
            result = handler(req, *args, **kwargs)
            if isinstance(result, Effect):
                return sync_perform(dispatcher, result)
            else:
                return result
