from doc2vec_eval import get_recommendations as d2v_get_recs
from algo_ii import populate_iks_dict
from algo_ii import predict_citations as iks_get_recs  # for "inverted keyword-score"... 
import socket
import time

HOST = ''
PORT = 6969  # 63696 for laptop; 6969, 36969, or 63969 for desktop

DOC2VEC_MODEL_FILE = 'file'   # TODO: Set filepath

# "Cached" 
d2v_model = None
authorities = {}

def initialize_models():
    """ Initialize our trained models once, so they can be reused.
    """
    from gensim.models.doc2vec import Doc2Vec
    d2v_model = Doc2Vec.load( DOC2VEC_MODEL_FILE )

    populate_iks_dict()

    import csv
    csv.field_size_limit( 2**30 )  # NOTE: was sys.maxsize. Failed on my system, for some reason
    with open( 'authorities_scores.csv', 'r' ) as auth_file:
        reader = csv.reader( data, delimiter=',', quotchar='\"' )
        for row in reader:
            authorities[ row[0] ] = float( row[1] )

# Found online:
def recv_timeout( sock ):
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
                data = clientsocket.recv(1024)  # TODO: Update buffer value  # NOTE: Use .decode() if python3
            except:
                break
            if data == '':
                break

            print( 'Received: '+ data )
            abstract, keys_scores = parse_input(data)
            #response = compute_recommendations( abstract, keys_scores )  # TODO: Enable this
            response = 'You sent: abstract = '+ abstract +'; keys_scores = '+ str(keys_scores)

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
    args = string.split('||')
    abstract = args[0]

    keywords_scores = {}
    keys_scores = args[1].split(';')
    for k_s in keys_scores:
        args = k_s.split(':')
        keywords_scores[ args[0] ] = float( args[1] )
    print( '- abstract = '+ abstract )
    print( '- keywords_scores = '+ str(keywords_scores) )
    return abstract, keywords_scores

def compute_recommendations( abstract, keywords_scores ):
    """ Given an abstract and keywords+scores,
        output reference recommendations as a string of comma-separated IDs (ints).
    """
    #d2v_rec_doc_ids = doc2vec_eval.get_recommendations( d2v_model, abstract )
    d2v_rec_doc_ids = d2v_get_recs( d2v_model, abstract )

    # TODO: The following function currently expects keywords+scores in a different format
    #       so either change this call or change the function.
    iks_rec_doc_ids = iks_get_recs( keywords_scores, authorities )

    # TODO: Finish this. Decide how we want to have an integrated solution
    #       Trivial solution: weights doc_ids higher that are obtained from both D2V and IKS

if __name__ == '__main__':
    #initialize_models()   # TODO: Enable this

    serve()
