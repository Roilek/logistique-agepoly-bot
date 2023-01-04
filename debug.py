import json

import truffe

# Use only for debugging

def create_debug_folder_if_needed():
    """Creates the debug folder if it doesn't exist"""
    import os
    if not os.path.exists('debug'):
        os.makedirs('debug')


def save_truffe_to_JSON():
    """Saves the truffe object to a JSON file"""
    # save JSON to file
    with open('debug/truffe.json', 'w') as f:
        json.dump(truffe._get_json_from_truffe(), f, indent=4)


if __name__ == '__main__':
    create_debug_folder_if_needed()
    save_truffe_to_JSON()
