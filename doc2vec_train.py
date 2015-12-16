# TODO: Test python3 vs. python2 unicode ! Hopefully trained models aren't affected......................

from doc2vec_eval import get_recommendations as d2ve_get_recommendations
from server import compute_recommendations as serv_get_recommendations
from server import initialize_authorities
from algo_ii import populate_iks_dict
import datetime
#from random import shuffle
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
#from nltk.tokenize import MWETokenizer
import pandas as pd
from random import shuffle
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

# TODO: Update as necessary
DBLP_TRAINING = 'data-kw-training.csv'
TEST_FILEPATH = 'data-kw-test.csv'

import re
spltr = re.compile( r'\W+' )

def clean_tokenize( string ):
    """ Given a string, output a list of its tokens--lowercase--and excluding punctuation.
    """
    return [ w for w in spltr.split( string.lower() ) if w != '' ]

def get_abstracts_indices_from_DBLP( filepath ):
    papers = pd.read_csv( filepath )
    for i, abstract in enumerate( papers['ABSTRACT'] ):
        index = papers['INDEX'][i]
        if isinstance( abstract, float ):
            #print( 'NO ABSTRACT FOUND at Index = '+ index )
            continue
        ab_words = clean_tokenize( abstract )
        if not USE_DBLP_IDS:
            tag_map.append( index )
            yield TaggedDocument( words=ab_words, tags=[i] )
        else:
            yield TaggedDocument( words=ab_words, tags=[int(index)] )  # TODO: Or try 'DBLP_'+str(index) ?
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
            yield TaggedDocument( words=ab_words, tags=[arXiv_start + i] )
        else: 
            yield TaggedDocument( words=ab_words, tags=[int(index)])  # TODO: Or try 'ARXIV_'+str(index) ?
    conn.close()


def get_docs():
    print( now() )
    print( 'Loading DBLP abstracts...' )
    docs = list( get_abstracts_indices_from_DBLP(DBLP_TRAINING) )
    if USE_ARXIV:
        print( 'Loading arXiv abstracts...' )
        docs += list( get_abstracts_indices_from_arXiv() )
    print( now() )
    print( 'Done loading abstracts.' )
    return docs


def get_paper_abstract( idx ):
    """ Given a model doc tag, output the respective DBLP or arXiv paper abstract"""
    return ' '.join( docs[idx].words )


def test_model( FULL_SIM, model, test_papers, keywords_docsrels, authorities ):
    hits = 0
    misses = 0

    highest_miss = 0
    miss_total = 0
    lowest_hit = 1
    hit_total = 0
    for i, abstract in enumerate( test_papers['ABSTRACT'] ):
        if i == 200:
            break
        index = test_papers['INDEX'][i]

        rec_refs = None
        # NOTE: If just testing the Doc2Vec model, use this:
        if not FULL_SIM:
            rec_refs = d2ve_get_recommendations( model, abstract, USE_DBLP_IDS )
        # NOTE: For testing Doc2Vec + AII:
        else:
            keywords_scores = test_papers['KEYWORDS'][i].split(';')
            del keywords_scores[-1]
            rec_refs = serv_get_recommendations( abstract, keywords_scores, model, keywords_docsrels, authorities )

        act_refs = test_papers['REF_ID'][i]
        if ';' in act_refs:
            act_refs = act_refs.split(';')
        else:
            act_refs = list( act_refs )
        act_refs = list( map(int, act_refs) )

        for rec_ref in rec_refs:
            if rec_ref[0] in act_refs:
                hits += 1
                hit_total += rec_ref[1]
                if rec_ref[1] < lowest_hit:
                    lowest_hit = rec_ref[1]
            else:
                misses += 1
                miss_total += rec_ref[1]
                if rec_ref[1] > highest_miss:
                    highest_miss = rec_ref[1]
        """
        print( 'hits = '+ str(hits) )
        if hits > 0:
            print( '  average hit = '+ str(hit_total/hits) )
        print( '  lowest hit  = '+ str(lowest_hit) )
        print( 'misses = '+ str(misses) )
        if misses > 0:
            print( '  average miss = '+ str(miss_total/misses) )
        print( '  highest miss = '+ str(highest_miss) )
        """

    print( 'hits = '+ str(hits) )
    if hits > 0:
        print( '  average hit = '+ str(hit_total/hits) )
    print( '  lowest hit  = '+ str(lowest_hit) )
    print( 'misses = '+ str(misses) )
    if misses > 0:
        print( '  average miss = '+ str(miss_total/misses) )
    print( '  highest miss = '+ str(highest_miss) )
    accuracy = hits / (hits + misses)
    print( "ACCURACY = "+ str(accuracy) )

    # TODO: Output for Xavier: doc_id, list of recs

def test_models( FULL_SIM, models_files ):
    test_papers = pd.read_csv( TEST_FILEPATH )

    # NOTE: Only need for testing with AII:
    keywords_docsrels = populate_iks_dict()
    authorities = initialize_authorities()

    for mod_f in models_files:
        print( 'Testing '+ mod_f )
        model = Doc2Vec.load( mod_f )
        print( 'Model loaded.' )

        test_model( FULL_SIM, model, test_papers, keywords_docsrels, authorities )

# TODO: Epochs was 12
def train_test_and_save_doc2vec( docs, epochs=3, dm=1, dm_concat=1, size=400, window=5, negative=5, hs=0, min_count=2 ):
    alpha, min_alpha = (0.025, 0.001)
    alpha_delta = (alpha - min_alpha) / epochs

    print( now() )
    print( 'Configuring Doc2Vec model...' )
    model = Doc2Vec( dm=dm, dm_concat=dm_concat, size=size, window=window, negative=negative, hs=hs, min_count=min_count, workers=cores )
    print( 'Building vocab at {}...'.format( now() ) )
    model.build_vocab( docs ) # TODO: Is this necessary?
    print( 'Done building vocab at {}.'.format( now() ) )
    for epoch in range( epochs ):
        # Shuffle docs for better results, gensim folks say
        shuffle( docs )

        print( 'Epoch #{} at {}'.format( epoch, now() ) )
        # TODO: Look into Doc2Vec.reset_from() and maybe use model[i].reset_from( model )
        #       (if we're training multiple different models in bulk)

        model.alpha, model.min_alpha = alpha, alpha   # Freeze learning rate
        model.train( docs )

        alpha -= alpha_delta
        print( 'Done training #{} at {}'.format( epoch, now() ) )

    test_model( model )

    filepath = ''
    if USE_DBLP_IDS:
        filepath = 'tagmap0'
    else:
        filepath = 'tagmap1'
    filepath += 'epochs{}dm{}dmc{}size{}win{}neg{}hs{}minc{}'.format( epochs,
        dm, dm_concat, size, window, negative, hs, min_count )
    print( 'Saving model to {}'.format( filepath ) )
    model.save( filepath )
    print( 'Done model save at {}'.format( now() ) )


if __name__ == '__main__':
    print( now() )

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'USE_DBLP_IDS':
        USE_DBLP_IDS = True

    FULL_SIM = False
    if len(sys.argv) > 2 and sys.argv[2] == 'FULL_SIM':
        FULL_SIM = True
    print( 'FULL_SIM = '+ str(FULL_SIM) )

    """
    tagmap0_models = ['models/tagmap0epochs12dm0dmc1size400win5neg5hs0minc2',
                      'models/tagmap0epochs12dm1dmc1size200win5neg5hs0minc2',
                      'models/tagmap0epochs12dm1dmc1size300win5neg5hs0minc2',
                      'models/tagmap0epochs12dm1dmc1size400win5neg5hs0minc2']
    """
    tagmap0_models = ['models/tagmap0epochs12dm0dmc1size400win5neg5hs0minc2']
    tagmap1_models = ['models/tagmap1epochs12dm0dmc1size400win5neg5hs0minc2',
                      'models/tagmap1epochs12dm1dmc1size200win5neg5hs0minc2',
                      'models/tagmap1epochs12dm1dmc1size300win5neg5hs0minc2',
                      'models/tagmap1epochs12dm1dmc1size400win5neg5hs0minc2']
    if not USE_DBLP_IDS:
        test_models( FULL_SIM, tagmap1_models )
    else:
        test_models( FULL_SIM, tagmap0_models )
    exit(0)  # TODO: Remove if doing training, too

    docs = get_docs()  # TODO: Update as necessary
    # TODO: Try setting different epochs for these models, amongst other changes

    # External test configurations:
    # PV-DM w/concatenation - window=5 (both sides) approximates paper's 10-word total window size
    train_test_and_save_doc2vec( docs, dm=1, dm_concat=1, size=400, window=5, negative=5, hs=0, min_count=2 )
    # PV-DBOW 
    train_test_and_save_doc2vec( docs, dm=0, size=400, negative=5, hs=0, min_count=2 )
    # PV-DM w/average
    # NOTE: This doesn't work?? because, evidently, 'dm_mean' is not an expected parameter?
    #train_test_and_save_doc2vec( docs, dm=1, dm_mean=1, size=400, window=10, negative=5, hs=0, min_count=2 )
    
    # Our test configurations:
    train_test_and_save_doc2vec( docs, size=200 )
    train_test_and_save_doc2vec( docs, size=300 )
    train_test_and_save_doc2vec( docs, size=400 )
