import unittest
import server_query

class TestServerConnectivity(unittest.TestCase):
    def test_server_query_success(self):
        ip = "216.245.177.69"
        port = 2323
        info, mods = server_query.query_server(ip, port)

        self.assertIsInstance(info, dict)
        self.assertIn("island", info)
        self.assertIsInstance(mods, list)
        self.assertGreater(len(mods), 0)

if __name__ == '__main__':
    unittest.main()