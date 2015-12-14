__author__ = 'julianalouback'


import csv
import sys
import re
import algo_ii

csv.field_size_limit( 2**27 )  # NOTE: was sys.maxsize

def clean(word):
    word =  word.lower()
    return re.sub(r"^\W+|\W+$", "", word)

def get_authorities():
    data= open('authorities_scores.csv', 'r')
    reader = csv.reader(data, delimiter=',', quotechar='\"')
    authorities = {}
    for row in reader:
        authorities[row[0]] = float(row[1])
    data.close()
    return authorities

# Runs algo_ii, writes to report.txt and to standard output (accuracy printed every 50 calculations)
def test():
    authorities = get_authorities()
    algo_ii.populate_iks_dict()

    report = open( 'report.txt', 'wb' )
    data = open('papers30000.csv', 'r')
    reader = csv.reader(data, delimiter=',', quotechar='\"')
    total_hits = 0
    count = 0
    total_citations = 0
    for row in reader:
        index = row[1]
        count += 1
        citations = row[6].split(';')
        keywords = row[9].split(';')
        del keywords[-1]
        total_citations += len(citations)
        recommendations = algo_ii.predict_citations( keywords, authorities )
        hits = 0
        for citation in citations:
            if recommendations.has_key(citation):
                hits += 1
        total_hits += hits
        print( index + " accuracy: " + str(hits) + "/" + str(len(citations)) + "\n" )
        report.write(index + " accuracy: " + str(hits) + "/" + str(len(citations)) + "\n")
        if (count % 50) == 0:
            print( "temp is:" )
            print( total_hits )
            print( "out of " )
            print( total_citations )
            print( "achieved accuracy:" )
            print( total_hits/float(total_citations) )
    report.close()
    data.close()

def _specific_test( papers, authorities, test_ids ):
    for pid in test_ids:
        print( 'ID = '+ pid )
        pid = int(pid)

        abstract = list( papers[papers['INDEX'] == pid]['ABSTRACT'] )[0]
        print( abstract[:45] +'...' )

        keywords = list( papers[papers['INDEX'] == pid]['KEYWORDS'] )[0].split(';')
        del keywords[-1]

        recommendations = algo_ii.predict_citations( keywords, authorities )

        citations = list( papers[papers['INDEX'] == pid]['REF_ID'] )[0].split(';')
        hits = 0
        for citation in citations:
            if recommendations.has_key(citation):
                hits += 1

        print( 'Recommendations for '+ str(pid) +':' )
        print( '> '+ str( sorted( recommendations.keys() ) ) )
        print( 'Actuals:\n> '+ str( sorted(citations) ) )
        print( 'Hits = '+ str(hits) +'\n' )

def specific_test():
    import pandas as pd
    # NOTE: The first row of data-kw.csv should be the header, i.e.:
    #       "INDEX","TITLE","AUTHORS","YEAR","PUB_VENUE","REF_ID","REF_NUM","ABSTRACT","KEYWORDS"
    papers = pd.read_csv( 'data-kw.csv' )

    authorities = get_authorities()
    algo_ii.populate_iks_dict()

    print( "HUMAN EVAL #1:\n" )
    _specific_test( papers, authorities, ['105542', '586892', '695628', '209104', '139162'] )
    print( "\n=================================\n" )

    print( "HUMAN EVAL #2:\n" )
    _specific_test( papers, authorities, ['751328', '619377', '686318', '283022', '591411'] )
    print( "\n=================================\n" )

    print( "HUMAN EVAL #3:\n" )
    _specific_test( papers, authorities, ['360556', '1022648', '1071218', '1112586', '451082'] )
    print( "\n=================================\n" )

    print( "HUMAN EVAL #4:\n" )
    _specific_test( papers, authorities, ['90992', '784131', '1080100', '96640', '503999'] )
    print( "\n=================================\n" )

if __name__ == '__main__':
    specific_test()
