__author__ = 'julianalouback'

import csv
import sys

csv.field_size_limit( 2**30 )   # was sys.maxsize

# Threshold for relevance of keywords
THRESHOLD = 0.6

def populate_iks_dict():
    keywords_docsrels = {}
    with open( 'keywordscores.csv', 'r' ) as iks_file:
        reader = csv.reader( iks_file, delimiter=',', quotechar='\"' )
        for row in reader:
            docsrels = row[1].split(';')
            del docsrels[-1]
            dr_tupes = []
            for dr in docsrels:
                d_r = dr.split(':')
                dr_tupes.append( (d_r[0], float(d_r[1])) )
            keywords_docsrels[ row[0] ] = dr_tupes
    return keywords_docsrels

"""
def get_relevance2( keywords ):
    # NOTE: What if we see a keyword (in 'keywords') that isn't in the dict?
    # We ignore it. (For now, at least.)
    all_scores = {}
    for keyword in keywords:
        if keyword in keywords_docsrels:
            all_scores[ keyword ] = keywords_docsrels[ keyword ]
    return all_scores

# For a list of keywords, returns a dict with keyword as key and list of doc:relevance_score values
def get_relevance(keywords):
    counter = 0
    all_scores = {}
    with open('keywordscores.csv', 'r') as data:
        reader = csv.reader(data, delimiter=',', quotechar='\"')
        for row in reader:
            kw = row[0]
            if kw in keywords:
                counter += 1
                scores = row[1].split(';')
                del scores[-1]
                all_scores[kw] = scores
                if counter == len(keywords):
                    break
    return all_scores
"""

def get_scores( keywords_docsrels, keywords ):
    # NOTE: What if we see a keyword (in 'keywords') that isn't in the dict?
    # We ignore it. (For now, at least.)
    docs = {}
    # Add doc relevance scores to doc entries
    for keyword in keywords:
        if keyword in keywords_docsrels:
            docsrels = keywords_docsrels[keyword]
            for entry in docsrels:
                doc = entry[0]
                score = entry[1]
                if doc not in docs:
                    docs[doc] = score
                else:
                    docs[doc] += score
	"""
    # Add authority score to doc entries, remove docs with 0 authority
    for doc in docs.keys():
        try:
            authority = authorities[doc]
            docs[doc] = docs[doc] + (100 * authority)
        except KeyError:
            del docs[doc]
	"""
    # Sort and return top 20
    return sorted( docs.iteritems(), key=lambda x:-x[1] )[:20]


def predict_citations( keywords_docsrels, candidates ):
    # TODO: Do we make sure all keywords are lower-cased and trimmed and such ??
    keywords = []
    for candidate in candidates:
        # TODO: We should probably drop keywords that contain ':'
        colon = candidate.rfind(':')
        keyword = candidate[:colon]
        # NOTE: Some keywords don't have a score, e.g. ID 747316's "durp" keyw
        try:
            relevance = float( candidate[colon+1:] )
        except ValueError:
            break
        # Ignore doc_ids less than threshold
        if relevance < THRESHOLD:
            break
        keywords.append(keyword)
    # list of top k recommended documents and a score
    return get_scores( keywords_docsrels, keywords )

if __name__ == '__main__':
    pass
