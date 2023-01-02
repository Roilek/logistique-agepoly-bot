import json

import truffe


def create_debug_folder_if_needed():
    import os
    if not os.path.exists('debug'):
        os.makedirs('debug')


def save_truffe_to_JSON():
    # save JSON to file
    with open('debug/truffe.json', 'w') as f:
        json.dump(truffe._get_json_from_truffe(), f, indent=4)


create_debug_folder_if_needed()
save_truffe_to_JSON()
