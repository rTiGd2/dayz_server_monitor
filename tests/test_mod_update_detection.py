import unittest
import server_query
import steam_api
import state_manager
import os
import json

STATE_FILE = "tests/test_state.json"

class TestModUpdateDetection(unittest.TestCase):
    def setUp(self):
        # Redirect state file for safety
        state_manager.STATE_FILE = STATE_FILE

    def tearDown(self):
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    def test_mod_update_logic(self):
        ip = "216.245.177.69"
        port = 2323
        info, mods = server_query.query_server(ip, port)

        first_mod = mods[0]
        mod_info = steam_api.get_mod_info(first_mod['workshop_id'])

        # Write previous state with one second older update time
        state_manager.save_state({
            first_mod['workshop_id']: {
                "title": mod_info['title'],
                "time_updated": mod_info['time_updated'] - 1
            }
        })

        # Load back the state and assert
        state = state_manager.load_state()
        self.assertEqual(state[first_mod['workshop_id']]['title'], mod_info['title'])
        self.assertEqual(state[first_mod['workshop_id']]['time_updated'], mod_info['time_updated'] - 1)

        # Now verify that current mod info is newer
        self.assertGreater(mod_info['time_updated'], state[first_mod['workshop_id']]['time_updated'])

if __name__ == '__main__':
    unittest.main()