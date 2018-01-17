import requests
import time
from all_params_reform import get_formatted_reform, REFORM, CG_REFORM

LOCAL_BASE_URL = "http://127.0.0.1:8000/taxbrain/"
TEST_BASE_URL = "http://ospc-taxes7.herokuapp.com/taxbrain/"
MINI_REFORM = {u'EITC_rt_0': 0.4,
               u'EITC_rt_1': 0.7,
               u'EITC_rt_2': 0.8,
               u'EITC_rt_3': 1.5}

DATA = {u'start_year': unicode(2017), u'csrfmiddlewaretoken': None,
        u'has_errors': [u'False']}


def get_session(url=LOCAL_BASE_URL):
    session = requests.Session()
    session.get(url)
    csrftoken = session.cookies['csrftoken']

    return session, csrftoken


def get_data(reform=REFORM):
    """read taxbrain styled reform"""
    DATA.update(get_formatted_reform(reform=reform))
    return DATA


def post_reform(session, data, files=None, url=LOCAL_BASE_URL):
    response = session.post(url, data=data, files=files)
    # assert response.status_code == 200
    print("RESPONSE", response)
    print("URL", response.url)

    pk = response.url[:-1].split('/')[-1]

    return session, pk, response


def post_file(session, data, reform_path, assump_path=None, url=None):
    if url is None:
        url = LOCAL_BASE_URL + 'file/'

    assert url.endswith('file/')
    files = {}
    reform_file = open(reform_path, 'r')
    files['docfile'] = reform_file
    if assump_path is not None:
        assump_file = open(assump_path, 'r')
        files['assumpfile'] = assump_file
    print(files)
    res = post_reform(session, data, files=files, url=url)

    reform_file.close()
    if assump_path is not None:
        assump_file.close()

    return res

# def wait(session, pk):
#     time.sleep(10)
#
#     print ('unique_url', unique_url)
#     result_response = s.get(unique_url)
#
#     print(result_response)
#     print(dir(result_response))
#     print(result_response.text)
#     print(result_response.status_code)
#     print(result_response.json)
#     result_json = result_response.json()
#     print(result_json)
#
#     while result_json['status_code'] == 202:
#         result_response = s.get(unique_url)
#         result_json = result_response.json()
#         print(result_response)
#         print(result_json)
#         time.sleep(5)
#
# def read_csv(session, pk):
#     # time.sleep(300)
#     print(result_json)
#     print('now getting csv?')
#     csv_url = unique_url + 'output.csv/'
#     r = s.get(csv_url)
#
#     print(r)
#     print(r.text)
