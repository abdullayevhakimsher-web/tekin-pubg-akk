import unittest

from bot import app, create_app


class BotStartupTests(unittest.TestCase):
    def test_app_can_be_created_and_has_root_route(self):
        recreated_app = create_app()
        self.assertIs(recreated_app, app)

        route_paths = {route.path for route in app.routes if hasattr(route, "path")}
        self.assertIn("/", route_paths)


if __name__ == "__main__":
    unittest.main()
