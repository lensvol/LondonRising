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
            decrypted_bytes = aes.decrypt(
                base64.decodebytes(
                    bytes(dict['json']['body'], 'ascii')))
            pad = decrypted_bytes[-1]
            unpadded = decrypted_bytes[:-pad]
            dict['json']['body'] = json.loads(unpadded.decode('utf-8'))
    except KeyError:
        pass
    return dict


db = sqlite3.connect('fallenlondonproduction.cblite')
c = db.cursor()
c.execute('select * from revs')

key = b"eyJUaXRsZSI6Ildo"

shutil.copyfile('fallenlondonproduction.cblite', 'decrypted.cblite')
db2 = sqlite3.connect('decrypted.cblite')
c2 = db2.cursor()
for x in c.fetchall():
    x = process_row(x, AES.new(key, AES.MODE_CBC, b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'))
    c2.execute('update revs set json=? where sequence=?', (json.dumps(x['json']), str(x['sequence'])))
db2.commit()