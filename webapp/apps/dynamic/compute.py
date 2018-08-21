from ..taxbrain.mock_compute import MockCompute
import requests_mock

class ElasticMockCompute(MockCompute):
    def remote_retrieve_results(self, theurl, params):
        self.count += 1
        text = ('{"elasticity_gdp": {"gdp_elasticity_1": "0.00310"}, '
                '"dropq_version": "0.6.a96303", "taxcalc_version": '
                '"0.6.10d462"}')
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_get_result', text=text)
            return DropqCompute.remote_retrieve_results(self, theurl, params)
