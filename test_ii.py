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
        count += 1
        #if count == 1:
        #    continue
        index = row[1]
        #if int(index) < 747313:
        #    continue
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

if __name__ == '__main__':
    import datetime
    print( datetime.datetime.now() )
    test()
    print( datetime.datetime.now() )
