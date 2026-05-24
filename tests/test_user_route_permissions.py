from fastapi.routing import APIRoute

from app.api.deps import get_current_admin_user, require_login
from app.main import app


def _user_route(path: str, method: str) -> APIRoute:
    for route in app.routes:
        if (
            isinstance(route, APIRoute)
            and route.path == path
            and method.upper() in route.methods
        ):
            return route
    raise AssertionError(f"Route not found: {method.upper()} {path}")


def _dependency_calls(route: APIRoute) -> set[object]:
    return {dependency.call for dependency in route.dependant.dependencies}


def test_user_admin_routes_require_admin_dependency() -> None:
    admin_routes = [
        ("POST", "/api/user/add"),
        ("GET", "/api/user/get"),
        ("POST", "/api/user/delete"),
        ("POST", "/api/user/update"),
        ("POST", "/api/user/list/page/vo"),
    ]

    for method, path in admin_routes:
        route = _user_route(path, method)

        assert get_current_admin_user in _dependency_calls(route)


def test_get_login_route_requires_login_dependency() -> None:
    route = _user_route("/api/user/get/login", "GET")

    assert require_login in _dependency_calls(route)


def test_public_user_routes_do_not_require_admin_dependency() -> None:
    public_routes = [
        ("POST", "/api/user/register"),
        ("POST", "/api/user/login"),
        ("POST", "/api/user/logout"),
        ("GET", "/api/user/get/vo"),
    ]

    for method, path in public_routes:
        route = _user_route(path, method)

        assert get_current_admin_user not in _dependency_calls(route)
