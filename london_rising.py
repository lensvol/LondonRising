#################################
#                               #
#         LONDON RISING         #
#   The Fallen London Reverse   #
#      Enginerring Project      #
#                               #
# This program is free and open #
#    source software released   #
#   GNU GPL 3 (see LICENCE for  #
#       further details).       #
#                               #
#################################

import sys
import json
import sqlite3
import base64
import shutil
import argparse
import os
import fl_types

try:
    import Crypto.Cipher.AES as AES
except ImportError:
    #  workaround for a bug in some Windows versions of Python
    import crypto
    sys.modules['Crypto'] = crypto
    import Crypto.Cipher.AES as AES

ORIG_FILE = "fallenlondonproduction.cblite"
DECRYPTED_FILE = "decrypted.cblite"
GRAPH_FILE = "fallenlondon.gexf"
KEY = b"eyJUaXRsZSI6Ildo"


def main(input_file, output_file, xcrypt, graphfile, big_graph):
    if big_graph:
        fl_types.IGNORE_FIELDS = []
        fl_types.GameObject.ignore_refs = []

    graphdata = FLGraph(graphfile)

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
        graphdata.add_graph_node(x)

    db2.commit()
    graphdata.write_to_file()


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


class FLGraph(object):
    def __init__(self, graphfile):
        if graphfile is None:
            self._should_skip = True
            return
        import networkx
        import functools
        self._should_skip = False
        self._G = networkx.MultiDiGraph()
        self._write_func = functools.partial(networkx.write_gexf, self._G, graphfile,
                                             encoding='utf-8', prettyprint=True)

    def add_graph_node(self, row_dict):
        if self._should_skip:
            return
        row_dict = self._flatten_node(row_dict)
        node, edges = fl_types.parse_dict_to_game_object(row_dict, self.add_graph_node)
        if node is not None:
            self._G.add_node(node[0], **node[1])
            self._G.add_edges_from(edges)
            return node[0]
        return None

    def write_to_file(self):
        if self._should_skip:
            return
        self._write_func()

    @classmethod
    def _flatten_node(cls, node):

        cls._parametrized_flatten(node, 'json')
        cls._parametrized_flatten(node, 'body')
        return node

    @classmethod
    def _parametrized_flatten(cls, node, param):
        try:
            for key in node[param]:
                node[key] = node[param][key]
            del node[param]
        except KeyError:
            pass
        return node


if __name__ == "__main__":
    # text ASCII art generated with http://patorjk.com/software/taag (font: Georgia 11)
    # ASCII Fanghat by me
    # (but the output of https://manytools.org/hacker-tools/convert-images-to-ascii-art/ was used as reference)
    print("""
7MMF'                                 `7MM                        
  MM                                     MM                        
  MM         ,pW"Wq.  `7MMpMMMb.    ,M""bMM   ,pW"Wq.  `7MMpMMMb.  
  MM        6W'   `Wb   MM    MM  ,AP    MM  6W'   `Wb   MM    MM  
  MM      , 8M     M8   MM    MM  8MI    MM  8M     M8   MM    MM  
  MM     ,M YA.   ,A9   MM    MM  `Mb    MM  YA.   ,A9   MM    MM  
.JMMmmmmMMM  `Ybmd9'  .JMML  JMML. `Wbmd"MML. `Ybmd9'  .JMML  JMML.

             ----------------------
             |&&&&&&&&&&&&&&&&&&&&|
             |&&&&&&&&&&&&/.     *|
             |@@@&&&&&&&&&&@@@&*.%|
             |@@@@@@@@@@@@@@@@@@#.|
             |@@@@@@@@@@@@@@@@#.. |
             |@@@@@@@@@@@@@@@@#.. |
             |&@@@@@@@@@@@@@@@@@#.|
       /----&(&@@@@@@@@@@@@@@@@@,@&----\  
      @&&&&&&&&&&&& &&&&&&&& &&&&&&&&&&&@                         Fallen London
     (%&&&&&&&&&&& ' &&&&&& ' &&&&&&&&&&&)          Reverse Engineering Project
      @&&&&&&&&&&&   &&&&&&   &&&&&&&&&&@
       \-------------------------------/  
               \                */        
                \  / v v v v.\  /
                 \/           \/
                 
              ,,            ,,                  
`7MM\"""Mq.    db            db                                     
  MM   `MM.                                                        
  MM   ,M9  `7MM  ,pP"Ybd `7MM  `7MMpMMMb.   .P"Ybmmm              
  MMmmdM9     MM  8I   `"   MM    MM    MM  :MI  I8                
  MM  YM.     MM  `YMMMa.   MM    MM    MM   WmmmP"                
  MM   `Mb.   MM  L.   I8   MM    MM    MM  8M                     
.JMML. .JMM..JMML.M9mmmP' .JMML..JMML  JMML. YMMMMMb               
                                            6'     dP              
                                            Ybmmmd'     
    """)
    parser = argparse.ArgumentParser(description=
                                     "Tools for reverse engineering databases from the Fallen London mobile app")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-e", "--encrypt", help="Encrypt instead of decrypting", action="store_true")
    group.add_argument("-g", "--graph", help="Create a graph of decrypted data", action="store_true")
    parser.add_argument("-i", "--infile", help=
                        "File to read from (default:"+ORIG_FILE+"for decryption," + DECRYPTED_FILE + " for encryption")
    parser.add_argument("-o", "--outfile", help="File to write to (default: like with infile, but swap encryption and" +
                                                " decryption)")
    parser.add_argument("--graphfile", help="Filename for graph output (ignored if no -g; default:" + GRAPH_FILE + ")")
    parser.add_argument("--big-graph", help="If true, we don't try to limit the number of nodes/edges and generate" +
                                            "a big graph. This makes Gephi mad so this isn't the default. This does" +
                                            "nothing if no -g.",
                        action='store_true')
    args = parser.parse_args()
    infile = args.infile if args.infile else DECRYPTED_FILE if args.encrypt else ORIG_FILE
    outfile = args.outfile if args.outfile else ORIG_FILE if args.encrypt else DECRYPTED_FILE
    func = encrypt_row if args.encrypt else decrypt_row
    graph = None if not args.graph else args.graphfile if args.graphfile else GRAPH_FILE
    big_graph_for_you = args.big_graph
    main(infile, outfile, func, graph, big_graph_for_you)

