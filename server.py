from algo_ii import populate_iks_dict
from algo_ii import predict_citations as aii_get_recs  # for "inverted keyword-score"... 
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

USE_DBLP_IDS = True

def initialize_models():
    """ Initialize our trained models once, so they can be reused.
    """
    print( 'Initializing models' )
    from gensim.models.doc2vec import Doc2Vec
    d2v_model = Doc2Vec.load( DOC2VEC_MODEL_FILE )
    d2v_model.train([])  # A work-around for https://github.com/piskvorky/gensim/issues/419

    if DOC2VEC_MODEL_FILE.startswith( 'tagmap1' ):
        USE_DBLP_IDS = False
    else:
        USE_DBLP_IDS = True

    keywords_docsrels = populate_iks_dict()

    import csv
    csv.field_size_limit( 2**30 )  # NOTE: was sys.maxsize. Failed on my system, for some reason
    authorities = {}
    with open( 'authorities_scores.csv', 'r' ) as auth_file:
        reader = csv.reader( auth_file, delimiter=',', quotechar='\"' )
        for row in reader:
            authorities[ row[0] ] = float( row[1] )

    return d2v_model, keywords_docsrels, authorities

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
        output reference recommendations as a list of DBLP doc indices.
    """
    print( 'DEBUG: USE_DBLP_IDS = ' + str(USE_DBLP_IDS) )

    d2v_docs_scores = d2v_get_recs( d2v_model, abstract, USE_DBLP_IDS )
    aii_docs_scores = aii_get_recs( keywords_docsrels, keywords_scores )
    docs_scores = {}
    for doc, score in d2v_docs_scores:
        if doc not in docs_scores:
            docs_scores[doc] = score
        else:
            docs_scores[doc] += score
    for doc, score in aii_docs_scores:
        if doc not in docs_scores:
            docs_scores[doc] = score
        else:
            docs_scores[doc] += score

    for doc in docs_scores:
        if doc in authorities:
            docs_scores[doc] += (100 * authorities[doc])
    ds_list = sorted( docs_scores.iteritems(), key=lambda x:-x[1] )

    for doc, score in ds_list:
        print( 'DEBUG: '+ str(doc) +' = '+ str(score) )

    doc_ids = [ x[0] for x in ds_list ]
    return doc_ids

def papers_details( doc_ids, papers ):
    """ Given a list of DBLP indices,
        return a JSON string containing their: titles, abstracts, authors, years.
    """
    full_json = []
    for pid in doc_ids:
        jso = {}
        pid = int(pid)  # TODO: Maybe have all DBLP ids as ints to begin with (in initialization)?
        try:
            title = list( papers[papers['INDEX'] == pid]['TITLE'] )[0]
            authors = list( papers[papers['INDEX'] == pid]['AUTHORS'] )[0]
            summary = list( papers[papers['INDEX'] == pid]['ABSTRACT'] )[0]
            year = list( papers[papers['INDEX'] == pid]['YEAR'] )[0]
            jso['title'] = title
            jso['authors'] = authors
            jso['summary'] = summary
            jso['year'] = str(year)
            full_json.append( jso )
        except:  # Probably an IndexError (which happens when 'pid' not in DB), but cover our bases
            pass
    return json.dumps( full_json )

def load_papers():
    import pandas as pd
    return pd.read_csv( 'data-kw.csv' )

if __name__ == '__main__':
    d2v_model, keywords_docsrels, authorities = initialize_models()
    papers = load_papers()

    serve( d2v_model, keywords_docsrels, authorities, papers )
