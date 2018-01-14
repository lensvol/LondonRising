#  this is a quick and dirty encrypt script for modifying the db
#  it sucks because it's mostly coopypasta from the decrypt one.
#  I'll do the more general version later, with cmdline params and shit

import Crypto.Cipher.AES as AES
import json
import sqlite3
import base64
import shutil


def process_row(row, aes):
    dict = {'sequence':       row[0],
            'doc_id':         row[1],
            'revid':          row[2],
            'parent':         row[3],
            'current':        row[4],
            'deleted':        row[5],
            'json':           json.loads(row[6]) if row[6] is not None else {},
            'no_attachments': row[7],
            'doc_type':       row[8]}
    try:
        if dict['json']['body']:
            to_encrypt = dict['json']['body']
            padlen = 16 - len(to_encrypt)%16
            to_encrypt += bytes(chr(padlen)*padlen, 'ascii')
            encrypted = aes.encrypt(to_encrypt)
            dict['json']['body'] = json.dumps(base64.encodebytes(encrypted).strip())
    except KeyError:
        pass
    return dict


db = sqlite3.connect('decrypted.cblite')
c = db.cursor()
c.execute('select * from revs')

key = b"eyJUaXRsZSI6Ildo"

shutil.copyfile('fallenlondonproduction.cblite', 'fallenlondonproduction.cblite.bak')
db2 = sqlite3.connect('fallenlondonproduction.cblite')
c2 = db2.cursor()
for x in c.fetchall():
    x = process_row(x, AES.new(key, AES.MODE_CBC, b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'))
    c2.execute('update revs set json=? where sequence=?', (json.dumps(x['json']), str(x['sequence'])))
db2.commit()
