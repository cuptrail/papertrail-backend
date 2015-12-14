# TODO: Check installation of:
#       cython
#       gensim

#from datetime.datetime import now
import datetime
#from random import shuffle
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
#from nltk.tokenize import MWETokenizer
from multiprocessing import cpu_count
cores = cpu_count()

def now():
    return datetime.datetime.now()

# Include arXiv CS papers
USE_ARXIV = False

# Use the IDs for papers/abstracts given in the DBLP dataset, or use 0-based indexing otherwise
# (this is mainly to deal with gensim's Doc2Vec quirks)
USE_DBLP_IDS = False

if not USE_DBLP_IDS:
    tag_map = []
    arXiv_start = 0

import re
spltr = re.compile( r'\W+' )

def clean_tokenize( string ):
    """ Given a string, output a list of its tokens--lowercase--and excluding punctuation.
    """
    return [ w for w in spltr.split( string.lower() ) if w != '' ]

def get_abstracts_indices_from_DBLP():
    import pandas as pd
    papers = pd.read_csv( 'data-kw.csv' )
    for i, abstract in enumerate( papers['ABSTRACT'] ):
        index = papers['INDEX'][i]
        if isinstance( abstract, float ):
            #print( 'NO ABSTRACT FOUND at Index = '+ index )
            continue
        ab_words = clean_tokenize( abstract )
        if not USE_DBLP_IDS:
            tag_map.append( index )
        yield TaggedDocument( words=ab_words, tags=[int(index)] )  # NOTE: WAS tags=[i]
        # NOTE: Consider having the list of references as multiple tags/labels?
        
def get_abstracts_indices_from_arXiv():
    from sqlite3 import connect
    if not USE_DBLP_IDS:
        arXiv_start = len( tag_map )
    conn = connect( 'paper_trail.db' )
    curs = conn.cursor()
    for i, row in enumerate( curs.execute( 'SELECT id, abstract FROM abstracts' ) ):
        index = row[0]
        abstract = row[1]
        ab_words = clean_tokenize( abstract )
        if not USE_DBLP_IDS:
            tag_map.append( index )
        yield TaggedDocument( words=ab_words, tags=[int(index)])  # NOTE: WAS tags=[arXiv_start + i]
    conn.close()


def transform_DBLP_data():
    """ Really only used for testing Bluemix... to save space
    """
    papers = pd.read_csv( 'data-kw.csv' )
    with open( 'DBLP_ids_abstracts.txt', 'w' ) as f:
        for i, abstract in enumerate( papers['ABSTRACT'] ):
            index = papers['INDEX'][i]
            f.write( str(index) + '|' + str(abstract) + '\n' )

def get_docs():
    print( now() )
    print( 'Loading DBLP abstracts...' )
    docs = list( get_abstracts_indices_from_DBLP() )
    if USE_ARXIV:
        print( 'Loading arXiv abstracts...' )
        docs += list( get_abstracts_indices_from_arXiv() )
    print( now() )
    print( 'Done loading abstracts.' )
    return docs


def get_paper_abstract( idx ):
    """ Given a model doc tag, output the respective DBLP or arXiv paper abstract"""
    return ' '.join( docs[idx].words )


def train_and_save_doc2vec( docs, epochs=1, dm=1, dm_concat=1, size=400, window=5, negative=5, hs=0, min_count=2 ):
    alpha, min_alpha = (0.025, 0.001)
    alpha_delta = (alpha - min_alpha) / epochs

    print( now() )
    print( 'Configuring Doc2Vec model...' )
    model = Doc2Vec( dm=dm, dm_concat=dm_concat, size=size, window=window, negative=negative, hs=hs, min_count=min_count, workers=cores )
    print( 'Building vocab at {}...'.format( now() ) )
    model.build_vocab( docs ) # TODO: Is this necessary?
    print( 'Done building vocab at {}.'.format( now() ) )
    for epoch in range( epochs ):
        print( 'Epoch 1 at {}'.format( now() ) )
        # TODO: Look into Doc2Vec.reset_from() and maybe use model[i].reset_from( model )
        #       (if we're training multiple different models in bulk)
        model.train( docs )
        print( 'Done training at {}'.format( now() ) )
        # TODO: Finish this. e.g. set and use alpha values, ...

    #return model
    filepath = 'epochs{}dm{}dm_concat{}size{}window{}negative{}hs{}min_count{}'.format( epochs,
        dm, dm_concat, size, window, negative, hs, min_count )
    print( 'Saving model to {}'.format( filepath ) )
    model.save( filepath )
    print( 'Done model save at {}'.format( now() ) )


if __name__ == '__main__':
    docs = get_docs()
    # TODO: Try setting different epochs for these models, amongst other changes

    # External test configurations:
    # PV-DM w/concatenation - window=5 (both sides) approximates paper's 10-word total window size
    train_and_save_doc2vec( docs, dm=1, dm_concat=1, size=400, window=5, negative=5, hs=0, min_count=2 )
    # PV-DBOW 
    train_and_save_doc2vec( docs, dm=0, size=400, negative=5, hs=0, min_count=2 )
    # PV-DM w/average
    # NOTE: This doesn't work?? because, evidently, 'dm_mean' is not an expected parameter?
    #train_and_save_doc2vec( docs, dm=1, dm_mean=1, size=400, window=10, negative=5, hs=0, min_count=2 )
    
    # Our test configurations:
    train_and_save_doc2vec( docs, size=200 )
    train_and_save_doc2vec( docs, size=300 )
    train_and_save_doc2vec( docs, size=400 )
