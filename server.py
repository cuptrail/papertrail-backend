from doc2vec_eval import get_recommendations as d2v_get_recs
from algo_ii import populate_iks_dict
from algo_ii import predict_citations as iks_get_recs  # for "inverted keyword-score"... 
import socket

HOST = ''
PORT = 63696  # 6969 or 63696 for laptop, 63969 for desktop

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
        (clientsocket, address) = s.accept()
        print( 'Connection established' )
        data = clientsocket.recv(1024).decode()  # TODO: Update buffer value
        print( 'Received: '+ data )

        #response = compute_recommendations( *parse_input(data) )  # TODO: Enable this
        response = 'DUMMY RESPONSE'

        print( 'Sending: '+ response )
        clientsocket.send( response.encode() )
        print( 'Response sent.' )
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
    #initialize_models()

    serve()
