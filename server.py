from algo_ii import populate_iks_dict
from algo_ii import predict_citations as iks_get_recs  # for "inverted keyword-score"... 
from doc2vec_eval import get_recommendations as d2v_get_recs
import json
import socket
import time

HOST = ''
PORT = 6969  # 63696 for laptop; 6969, 36969, or 63969 for desktop

DOC2VEC_MODEL_FILE = 'epochs1dm0dm_concat1size400window5negative5hs0min_count2'   # TODO: Set filepath

# "Cached"  NOTE: Doesn't seem to work... what are we missing?
#d2v_model = None
#authorities = {}
#keywords_docsrels = {}

def initialize_models():
    """ Initialize our trained models once, so they can be reused.
    """
    print( 'Initializing models' )
    from gensim.models.doc2vec import Doc2Vec
    d2v_model = Doc2Vec.load( DOC2VEC_MODEL_FILE )

    keywords_docsrels = populate_iks_dict()

    import csv
    csv.field_size_limit( 2**30 )  # NOTE: was sys.maxsize. Failed on my system, for some reason
    authorities = {}
    with open( 'authorities_scores.csv', 'r' ) as auth_file:
        reader = csv.reader( auth_file, delimiter=',', quotechar='\"' )
        for row in reader:
            authorities[ row[0] ] = float( row[1] )

    return d2v_model, keywords_docsrels, authorities

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

def serve( d2v_model, keywords_docsrels, authorities, papers ):
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
            doc_ids = compute_recommendations( abstract, keys_scores, d2v_model, keywords_docsrels, authorities )
            print( 'DEBUG: rec doc ids = '+ str(doc_ids) )

            response = papers_details( doc_ids, papers )
            response += '\n'   # NOTE: Apparently needed for Bluemix client code

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
    # TODO: Finish this. This is probably temporary code.
    abstract = ''
    keywords_scores = []
    try:
        args = string.split('||')
        abstract = args[0]  # TODO: CLEAN_TOKENIZE THIS!
        keywords_scores = [ x.strip() for x in args[1].split(';') ]
    except:
        pass
    print( '- abstract = '+ abstract )
    print( '- keywords_scores = '+ str(keywords_scores) )
    return abstract, keywords_scores

def compute_recommendations( abstract, keywords_scores, d2v_model, keywords_docsrels, authorities ):
    """ Given an abstract and keywords+scores,
        output reference recommendations as a string of comma-separated IDs (ints).
    """
	#d2v_rec_doc_ids = d2v_get_recs( d2v_model, abstract )  # TODO: Enable this

    # TODO: The following function currently expects keywords+scores in a different format
    #       so either change this call or change the function.

    iks_rec_doc_ids = iks_get_recs( keywords_docsrels, keywords_scores, authorities )

    doc_ids = [ x[0] for x in iks_rec_doc_ids ]  # TODO: Replace this with permanent solution

    return doc_ids

    # TODO: Finish this. Decide how we want to have an integrated solution
    #       Trivial solution: weights doc_ids higher that are obtained from both D2V and IKS

def papers_details( doc_ids, papers ):
    """ Given a list of DBLP indices,
        return a JSON string containing their: titles, abstracts, authors, years.
    """
    full_json = []
    for pid in doc_ids:
        jso = {}
        pid = int(pid)  # TODO: Maybe have all DBLP ids as ints to begin with (in initialization)?
        title = list( papers[papers['INDEX'] == pid]['TITLE'] )[0]
        authors = list( papers[papers['INDEX'] == pid]['AUTHORS'] )[0]
        summary = list( papers[papers['INDEX'] == pid]['ABSTRACT'] )[0]
        year = list( papers[papers['INDEX'] == pid]['YEAR'] )[0]
        jso['title'] = title
        jso['authors'] = authors
        jso['summary'] = summary
        jso['year'] = str(year)
        full_json.append( jso )
    return json.dumps( full_json )

def load_papers():
    import pandas as pd
    return pd.read_csv( 'data-kw.csv' )

if __name__ == '__main__':
    d2v_model, keywords_docsrels, authorities = initialize_models()
    papers = load_papers()

    serve( d2v_model, keywords_docsrels, authorities, papers )
