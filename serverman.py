import argparse
import json
import os
import secrets
import shutil
import unicodedata

from paths import CONFIGFILE, DIR_RES

# --- util

def normalize(texto:str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# --- input handling

def erase_data(force:bool=False):
    if not os.path.exists(DIR_RES):
        print('Data were already erased before.')
        exit(0)
    resp = 'Y' if force else \
            input('Are you sure you want '
                  'to erase the whole data?\n'
                  'This action can not be undone [y/N]: ').upper()
    if resp.startswith('Y'):
        shutil.rmtree(DIR_RES)
        print('Data was erased successfully!')
    else:
        print('The operation was canceled!')
    exit(0)

def config_server(force_overwriting:bool=False):
    if os.path.exists(CONFIGFILE):
        resp = 'Y' if force_overwriting else \
               input('The config file already exists. '
                     'If you proceed, the file will be overwritten.\n'
                     'Do you want to proceed with this operation [y/N]: ').upper()
        if not resp.startswith('Y'):
            print('The operation was canceled!')
            exit(0)
    cfg_d = {
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///minibookapi.db',
        'TOKEN': secrets.token_hex(32),
        'TOKEN_ADMIN': secrets.token_hex(32),
        'PIX_NAME': '',
        'PIX_KEY': ''
    }
    print(
        "This server uses Pix as a payment method.\n"
        "Please provide the receiver's name and Pix key.\n"
    )
    cfg_d['PIX_NAME'] = normalize(input('Pix receiver\'s name: '))
    cfg_d['PIX_KEY'] = input('Pix receiver\'s key: ')
    with open(CONFIGFILE, 'w', encoding='utf-8') as cfg_f:
        json.dump(cfg_d, cfg_f, ensure_ascii=False, indent=4)
    print('A new config.json file was created!')

def handle_input():
    parser = argparse.ArgumentParser(
        description='This is the Mini Book Api Server Manager.'
    )
    parser.add_argument(
        '-e', '--erase-data',
        action='store_true',
        help='This option erase the database.'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force an operation without prompting and/or protection.'
    )
    args = parser.parse_args()
    if args.erase_data:
        erase_data(args.force)
    else:
        config_server(args.force)

if __name__ == '__main__':
    try:
        handle_input()
    except KeyboardInterrupt:
        print("\nBye bye :)")
        exit(0)
