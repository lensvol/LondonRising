import sys
import json
import sqlite3
import base64
import shutil
import argparse
import os
try:
    import Crypto.Cipher.AES as AES
except ImportError:
    #  workaround for a bug in some Windows versions of Python
    import crypto
    sys.modules['Crypto'] = crypto
    import Crypto.Cipher.AES as AES

DECRYPTED_FILE = "decrypted.cblite"
ORIG_FILE = "fallenlondonproduction.cblite"
KEY = b"eyJUaXRsZSI6Ildo"


def main(input_file, output_file, xcrypt):
    #  TODO: graph generation (targeting gephi?)
    db = sqlite3.connect(input_file)
    c = db.cursor()
    c.execute('select * from revs')

    if os.path.isfile(output_file):
        shutil.copyfile(output_file, output_file + ".bak")

    shutil.copyfile(input_file, output_file)
    db2 = sqlite3.connect(output_file)
    c2 = db2.cursor()
    for x in c.fetchall():
        x = xcrypt(x, AES.new(KEY, AES.MODE_CBC, b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'))
        c2.execute('update revs set json=? where sequence=?', (json.dumps(x['json']), str(x['sequence'])))
    db2.commit()


def decrypt_row(row, aes):
    row_dict = db_row_to_dict(row)
    try:
        if row_dict['json']['body']:
            decrypted_bytes = aes.decrypt(
                base64.decodebytes(
                    encode_to_bytes(row_dict['json']['body'])))
            pad = decrypted_bytes[-1]
            unpadded = decrypted_bytes[:-pad]
            row_dict['json']['body'] = json.loads(unpadded.decode('utf-8'))
    except KeyError:
        pass
    return row_dict


def encrypt_row(row, aes):
    row_dict = db_row_to_dict(row)
    try:
        if row_dict['json']['body']:
            to_encrypt = encode_to_bytes(json.dumps(row_dict['json']['body']))
            padlen = 16 - len(to_encrypt) % 16
            to_encrypt += bytes(chr(padlen) * padlen, 'utf-8')
            encrypted = aes.encrypt(to_encrypt)
            row_dict['json']['body'] = base64.encodebytes(encrypted).strip().decode('utf-8')
    except KeyError:
        pass
    return row_dict


def db_row_to_dict(row):
    row_dict = {'sequence': row[0],
                'doc_id': row[1],
                'revid': row[2],
                'parent': row[3],
                'current': row[4],
                'deleted': row[5],
                'json': json.loads(decode_from_bytes(row[6])) if row[6] is not None else {},
                'no_attachments': row[7],
                'doc_type': row[8]}
    return row_dict


def decode_from_bytes(x):
    return x.decode('utf-8') if type(x) is bytes else x


def encode_to_bytes(x):
    return bytes(x, 'utf-8') if type(x) is str else x


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
                                     "Tools for reverse engineering databases from the Fallen London mobile app", )
    parser.add_argument("-e", "--encrypt", help="Encrypt instead of decrypting", action="store_true")
    parser.add_argument("-i", "--infile", help=
    "File to read from (default:" + ORIG_FILE + "for decryption, " + DECRYPTED_FILE +
    " for encryption")
    parser.add_argument("-o", "--outfile", help="File to write to (default: like with infile, but swap encryption and" +
                                                " decryption)")
    args = parser.parse_args()
    infile = args.infile if args.infile else DECRYPTED_FILE if args.encrypt else ORIG_FILE
    outfile = args.outfile if args.outfile else ORIG_FILE if args.encrypt else DECRYPTED_FILE
    func = encrypt_row if args.encrypt else decrypt_row
    main(infile, outfile, func)
