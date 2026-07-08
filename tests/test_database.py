import unittest
from sentry_mirror.database import infer_schema_from_json, get_json_type

class TestDatabase(unittest.TestCase):
    def test_get_json_type(self):
        self.assertEqual(get_json_type(1)["type"], "integer")
        self.assertEqual(get_json_type("test")["type"], "string")
        self.assertEqual(get_json_type(True)["type"], "boolean")
        self.assertEqual(get_json_type(None)["type"], "null")
        self.assertEqual(get_json_type(1.1)["type"], "number")
        self.assertEqual(get_json_type([])["type"], "array")
        self.assertEqual(get_json_type({})["type"], "object")

    def test_infer_schema_from_json(self):
        data = {"id": 1, "name": "John", "active": True}
        schema = infer_schema_from_json(data, "/api/users")
        self.assertEqual(schema.possible_table, "users")
        self.assertIn("id", schema.fields)
        self.assertEqual(schema.fields["id"].sql_type, "INTEGER")
        self.assertEqual(schema.fields["name"].sql_type, "TEXT")

if __name__ == '__main__':
    unittest.main()
