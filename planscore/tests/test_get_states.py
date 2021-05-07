import unittest, unittest.mock
import json
from .. import get_states, data

class TestGetStates (unittest.TestCase):

    def test_lambda_handler(self):
        states = data.State.__members__
        houses = data.House.__members__
    
        response = get_states.lambda_handler(None, None)
        
        self.assertEqual(response['statusCode'], '200')
        
        for (state, house) in json.loads(response['body']):
            self.assertIn(state, states)
            self.assertIn(house, houses)
