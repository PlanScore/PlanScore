import unittest, unittest.mock
import json
from .. import api_states, data

class TestAPIStates (unittest.TestCase):

    def test_lambda_handler(self):
        states = data.State.__members__
        houses = data.House.__members__
    
        response = api_states.lambda_handler(None, None)
        
        self.assertEqual(response['statusCode'], '200')
        
        for (state, house) in json.loads(response['body']):
            self.assertIn(state, states)
            self.assertIn(house, houses)
