from collections import namedtuple

PostMeta = namedtuple(
    'PostMeta',
    ['request',
     'personal_inputs',
     'json_reform',
     'model',
     'stop_submission',
     'has_errors',
     'errors_warnings',
     'start_year',
     'data_source',
     'do_full_calc',
     'is_file',
     'reform_dict',
     'assumptions_dict',
     'reform_text',
     'assumptions_text',
     'submitted_ids',
     'max_q_length',
     'user',
     'url']
)

BadPost = namedtuple('BadPost', ['http_response_404', 'has_errors'])
