from doc2vec_eval import get_recommendations as d2v_get_recs
from algo_ii import populate_iks_dict
from algo_ii import predict_citations as iks_get_recs  # for "inverted keyword-score"... 
import socket
import time

HOST = ''
PORT = 6969  # 63696 for laptop; 6969, 36969, or 63969 for desktop

DOC2VEC_MODEL_FILE = 'epochs1dm0dm_concat1size400window5negative5hs0min_count2'   # TODO: Set filepath

# "Cached" 
d2v_model = None
authorities = {}

USE_DBLP_IDS = False

def initialize_models():
    """ Initialize our trained models once, so they can be reused.
    """
    from gensim.models.doc2vec import Doc2Vec
    d2v_model = Doc2Vec.load( DOC2VEC_MODEL_FILE )

    if DOC2VEC_MODEL_FILE.startswith( 'tagmap1' ):
        USE_DBLP_IDS = False
    else:
        USE_DBLP_IDS = True

    populate_iks_dict()

    import csv
    csv.field_size_limit( 2**30 )  # NOTE: was sys.maxsize. Failed on my system, for some reason
    with open( 'authorities_scores.csv', 'r' ) as auth_file:
        reader = csv.reader( auth_file, delimiter=',', quotechar='\"' )
        for row in reader:
            authorities[ row[0] ] = float( row[1] )

# Found on code.activstate.com/recipes/408859:
def recv_timeout( sock ):
    """ Get the full message sent by the client, returned as one string.
    """
    sock.set_blocking( 0 )
    all_data = []; data = ''; begin = time.time()
    while True:
        now = time.time()
        if (total_data and now - begin > 2) or (now - begin > 4):
            break
        try:
            data = sock.recv(8192)
            if data:
                all_data.append( data )
                begin = time.time()
            else:
                time.sleep( 0.1 )
        except:
            pass
    return ''.join( all_data )

def serve():
    """ Listen and respond indefinitely.
    """
    print( 'Starting server' )
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    #s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    s.bind( (HOST, PORT) )
    s.listen( 5 )
    print( 'Server listening' )
    while True:
        clientsocket, address = s.accept()
        print( 'Connection established with '+ str(address) )

        while True:
            date = ''
            try:
                # TODO: Use recv_timeout() instead ?
                data = clientsocket.recv(8192)  # TODO: Update buffer value  # NOTE: Use .decode() if python3
            except:
                break
            if data == '':
                break

            print( 'Received: '+ data )
            abstract, keys_scores = parse_input(data)
            response = 'echo_abstract='+ abstract +';echo_keys_scores='+ str(keys_scores)
            response += ';recs='+ str( compute_recommendations( abstract, keys_scores ) )

            print( 'Sending: '+ response )
            try:
                clientsocket.send( response )  # NOTE: Use .encode() if python3
                print( 'Response sent.' )
            except:
                print( 'Response failed.')
                break  # TODO: Right?

        clientsocket.close()
        print( 'Connection with '+ str(address) +' closed' )
    print( 'Server done' )

def parse_input( string ):
    """ Given a string (sent via socket), extract the abstract and keywords+scores.
    """
    # TODO: Finish this. This is probably very temporary code.
    abstract = ''
    keywords_scores = {}
    try:
        args = string.split('||')
        abstract = args[0]

        keywords_scores = {}
        keys_scores = args[1].split(';')
        for k_s in keys_scores:
            args = k_s.split(':')
            keywords_scores[ args[0] ] = float( args[1] )
    except:
        pass
    print( '- abstract = '+ abstract )
    print( '- keywords_scores = '+ str(keywords_scores) )
    return abstract, keywords_scores

def compute_recommendations( abstract, keywords_scores ):
    """ Given an abstract and keywords+scores,
        output reference recommendations as a string of comma-separated IDs (ints).
    """
	d2v_rec_doc_ids = d2v_get_recs( d2v_model, abstract, USE_DBLP_IDS )  # TODO: Enable this

    # TODO: The following function currently expects keywords+scores in a different format
    #       so either change this call or change the function.
    iks_rec_doc_ids = iks_get_recs( keywords_scores, authorities )

    shared_doc_ids = set( set(d2v_rec_doc_ids).intersect( set(iks_rec_doc_ids) ) )

    return iks_rec_doc_ids  # TODO: Replace this with permanent solution

    # TODO: Finish this. Decide how we want to have an integrated solution
    #       Trivial solution: weights doc_ids higher that are obtained from both D2V and IKS

if __name__ == '__main__':
    initialize_models()

    serve()
