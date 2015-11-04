import requests
import time
from celery_status_server import server_url
def test_celery_status_server():
    for repeat in range(2):
        ticket_id = requests.post('{0}/example_async'.format(server_url)).json().get('ticket_id','')
        register = requests.post('{0}/register_job'.format(server_url),
                                  params={'ticket_id': ticket_id,
                                      'email': ticket_id,
                                      'callback':'google.com'})
        for retries in range(10):
            running = requests.get('{0}/celery_status_server'.format(server_url))
            print("ticket_id", ticket_id)
            try:
                running = running.json()
            except Exception as e:
                print(running._content)
                print('the above failed to .json() with ', e)
                raise
            try:
                print('ticket_id', ticket_id)
                print('RUNNING:', running)
                assert ticket_id in running
                if not 'callback_response' in running[ticket_id]:
                    assert 'inputs' in running[ticket_id]
                    assert 'status' in running[ticket_id]
                    assert 'eta' in running[ticket_id]
                    assert 'email' in running[ticket_id]['inputs']
                    assert 'started' in running[ticket_id]['inputs']
                    assert running[ticket_id]['inputs']['email'] == 'email.com'
                break
            except Exception as err:
                print('skipping', err)
                time.sleep(6)
                if retries == 9:
                    raise
    for ticket_id in running:
        requests.post('{0}/pop_ticket_id'.format(server_url),
                       params={'ticket_id': ticket_id})
    print(requests.get('{0}/celery_status_server'.format(server_url)).json())
    print('ok')
if __name__ == "__main__":
    test_celery_status_server()