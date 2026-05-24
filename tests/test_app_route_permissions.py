from fastapi.routing import APIRoute

from app.api.deps import get_current_admin_user, require_login
from app.main import app


def _app_route(path: str, method: str) -> APIRoute:
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


def test_app_user_routes_require_login_dependency() -> None:
    user_routes = [
        ("POST", "/api/app/add"),
        ("POST", "/api/app/update"),
        ("POST", "/api/app/delete"),
        ("POST", "/api/app/my/list/page/vo"),
    ]

    for method, path in user_routes:
        route = _app_route(path, method)

        assert require_login in _dependency_calls(route)


def test_app_admin_routes_require_admin_dependency() -> None:
    admin_routes = [
        ("POST", "/api/app/admin/delete"),
        ("POST", "/api/app/admin/update"),
        ("POST", "/api/app/admin/list/page/vo"),
        ("GET", "/api/app/admin/get/vo"),
    ]

    for method, path in admin_routes:
        route = _app_route(path, method)

        assert get_current_admin_user in _dependency_calls(route)


def test_public_app_routes_do_not_require_login_or_admin_dependency() -> None:
    public_routes = [
        ("GET", "/api/app/get/vo"),
        ("POST", "/api/app/good/list/page/vo"),
    ]

    for method, path in public_routes:
        route = _app_route(path, method)
        dependency_calls = _dependency_calls(route)

        assert require_login not in dependency_calls
        assert get_current_admin_user not in dependency_calls
