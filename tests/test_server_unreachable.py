import unittest
import server_query

class TestServerUnreachable(unittest.TestCase):
    def test_server_query_failure(self):
        ip = "216.245.177.69"
        port = 1  # guaranteed failure

        with self.assertRaises(Exception):
            server_query.query_server(ip, port)

if __name__ == '__main__':
    unittest.main()