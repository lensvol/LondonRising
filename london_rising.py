import sys
import json
import sqlite3
import base64
import shutil
try:
    import Crypto.Cipher.AES as AES
except ImportError:
    #  workaround for a bug in some Windows versions of Python
    import crypto
    sys.modules['Crypto'] = crypto


def main():
    #  TODO: argparsing
    #  TODO: graph generation (targeting gephi?)
    db = sqlite3.connect('fallenlondonproduction.cblite')
    c = db.cursor()
    c.execute('select * from revs')

    key = b"eyJUaXRsZSI6Ildo"

    shutil.copyfile('fallenlondonproduction.cblite', 'decrypted.cblite')
    db2 = sqlite3.connect('decrypted.cblite')
    c2 = db2.cursor()
    for x in c.fetchall():
        x = decrypt_row(x, AES.new(key, AES.MODE_CBC, b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'))
        c2.execute('update revs set json=? where sequence=?', (json.dumps(x['json']), str(x['sequence'])))
    db2.commit()


def decrypt_row(row, aes):
    row_dict = db_row_to_dict(row)
    try:
        if row_dict['json']['body']:
            decrypted_bytes = aes.decrypt(
                base64.decodebytes(
                    bytes(row_dict['json']['body'], 'ascii')))
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
            to_encrypt = bytes(json.dumps(row_dict['json']['body']), 'utf-8')
            padlen = 16 - len(to_encrypt) % 16
            to_encrypt += bytes(chr(padlen)*padlen, 'utf-8')
            encrypted = aes.encrypt(to_encrypt)
            row_dict['json']['body'] = base64.encodebytes(encrypted).strip().decode('utf-8')
    except KeyError:
        pass


def db_row_to_dict(row):
    row_dict = {'sequence': row[0],
                'doc_id': row[1],
                'revid': row[2],
                'parent': row[3],
                'current': row[4],
                'deleted': row[5],
                'json': json.loads(row[6]) if row[6] is not None else {},
                'no_attachments': row[7],
                'doc_type': row[8]}
    return row_dict


if __name__ == "__main__":
    main()
