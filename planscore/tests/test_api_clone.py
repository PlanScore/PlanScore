import unittest
import unittest.mock
from .. import api_clone, data


class TestApiClone(unittest.TestCase):

    @unittest.mock.patch('planscore.api_clone.data.MODELS')
    def test_get_current_model_returns_last_version_when_none(self, mock_models):
        ''' When dest_model_version is None, get_current_model should return the LAST version in the list.
        '''
        # Create a test model with multiple versions, oldest to newest
        test_versions = ['2019Z', '2022F', '2025A']
        src_model = data.Model(
            state=data.State.XX,
            house=data.House.ushouse,
            seats=4,
            incumbency=True,
            versions=test_versions,
            key_prefix='data/XX/test'
        )

        # Mock the MODELS list to include our test model
        mock_models.__iter__.return_value = [src_model]

        # Call get_current_model with None for dest_model_version
        result_version, result_model = api_clone.get_current_model(None, src_model)

        # Should return the LAST version (newest), not the first (oldest)
        self.assertEqual(result_version, '2025A',
            f'Expected last version "2025A" but got "{result_version}". '
            f'When model_version is unspecified, should default to newest version.')
        self.assertEqual(result_model.versions, test_versions)

    @unittest.mock.patch('planscore.api_clone.data.MODELS')
    def test_get_current_model_with_specified_version(self, mock_models):
        ''' When dest_model_version is specified, get_current_model should return that version.
        '''
        test_versions = ['2019Z', '2022F', '2025A']
        src_model = data.Model(
            state=data.State.XX,
            house=data.House.ushouse,
            seats=4,
            incumbency=True,
            versions=test_versions,
            key_prefix='data/XX/test'
        )

        # Mock the MODELS list to include our test model
        mock_models.__iter__.return_value = [src_model]

        # Call get_current_model with a specific version
        result_version, result_model = api_clone.get_current_model('2022F', src_model)

        # Should return the specified version
        self.assertEqual(result_version, '2022F')
        self.assertEqual(result_model.versions, test_versions)
