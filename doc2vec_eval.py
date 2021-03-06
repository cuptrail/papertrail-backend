from gensim.models.doc2vec import Doc2Vec, TaggedDocument
#from nltk.tokenize import MWETokenizer

#from doc2vec_train import clean_tokenize

# To be used? See doc2vec_train.py for how they're created/used
#tag_map
#arXiv_start

import re
spltr = re.compile( r'\W+' )

def clean_tokenize( string ):
    """ Given a string, output a list of its tokens--lowercase--and excluding punctuation.
    """
    return [ w for w in spltr.split( string.lower() ) if w != '' ]

from numpy import dot, sqrt, argmax

# Based on code found at nycdatascience.com:
def cossim( v1, v2 ):
    return dot(v1, v2) / sqrt( dot(v1, v1) * dot(v2, v2) )

def argmaxn( l, n ):
    l_copy = list(l)
    args = []
    for i in range(n):
        arg = argmax(l_copy)
        args.append(arg)
        l_copy[arg] = -float('inf')
    return args


def get_recommendations( model, abstract, USE_DBLP_IDS ):
    """ Given a model and abstract (as a single string),
        output a list of pairs: documents and their relevance scores
        where the number of pairs is limited by the threshold and/or a constant.
    """
    vec = model.infer_vector( clean_tokenize(abstract) )

    most_sim = 10
    # Code you'll find on nycdatascience.com:
    cossims = list( map( lambda v: cossim(vec, v), model.docvecs ) )
    sim_ids = argmaxn( cossims, most_sim )
    #for i in range(most_sim):
    #    print( sim_ids[i], cossims[sim_ids[i]] )

    docs_scores = None
    if not USE_DBLP_IDS:
        docs_scores = [ (tag_map[i], float(cossims[sim_ids[y]])) for y,i in enumerate(sim_ids) ]
    else:
        docs_scores = [ (i, float(cossims[sim_ids[y]])) for y,i in enumerate(sim_ids) ]

    # TODO: Change me:
    docs_scores = [ (x,y) for x,y in docs_scores if y >= 0.3 ]  # 0.415 seems to be middleground of avg hits/misses
    return docs_scores

def get_recommendations_for_index( model, index ):
    doc_ids = None
    if not USE_DBLP_IDS:
        doc_ids = [ tag_map[index] for index, _ in model.docvecs.most_similar( index ) ]
    else:
        doc_ids = [ index for index, _ in model.docvecs.most_similar( index ) ]
    return doc_ids


# ============================


def _quick_d2v_test( model ):
    test_idx = 397
    compare = 3

    compare = min( compare, 10 )
    print( 'TEST ABSTRACT:\n' + get_paper_abstract(test_idx) )
    print( '\n  SIMILAR TO:\n' )
    for idx_score in model.docvecs.most_similar( test_idx )[:compare]:
        print( get_paper_abstract(idx_score[0]) )
        print( '  (id = '+ str(idx_score[0]) + ', with a score of '+ str(idx_score[1]) +')\n' )

def check_recommendations( recs, acts ):
    """ recs = list of doc IDs as the recommended references/citations
        acts = list of doc IDs as the actual references/citations
        NOTE: the indices are given as the 'docs' indices, which then refer to actual doc IDs
    """
    matches = 0
    nomatches = 0
    for rec in recs:
        if rec in acts:
            matches += 1
        else:
            nomatches += 1
    return matches, nomatches

def get_references( index ):
    """ Given a 'docs' index, get the respective document's references
    """
    if index >= arXiv_start:
        print( "DEBUG: WE DON'T HAVE REFERENCES FOR THE ARXIV PAPERS" )
        return []
    refs = list( papers[papers['INDEX'] == tag_map[index]]['REF_ID'] )
    if ';' in refs[0]:
        refs = refs[0].split(';')
    refs = list( map(int, refs) )
    return refs

"""
def get_recommendations( index ):
    # TODO: Update this with infer_vector stuff
    #       and better logic in general.
    #doc_ids = [ tag_map[index] for index, _ in model.docvecs.most_similar( index) ]
    
    most_sim = 10
    vec = model.infer_vector( get_paper_abstract(index).split() )
    # Code you'll find on nycdatascience.com:
    cossims = list( map( lambda v: cossim(vec, v), model.docvecs ) )
    sim_ids = argmaxn( cossims, most_sim )
    #for i in range(most_sim):
        #print( sim_ids[i], cossims[sim_ids[i]] )
    doc_ids = [ tag_map[i] for i in sim_ids ]
    return doc_ids
"""

def _full_d2v_test():
    tot_matches = 0
    tot_nomatches = 0
    for test in range(1000):
        recs = get_recommendations( test )
        refs = get_references( test )
        matches, nomatches = check_recommendations( recs, refs )
        tot_matches += matches
        tot_nomatches += nomatches
    print( str(tot_matches) + " " + str(tot_nomatches) )
