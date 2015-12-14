def _test_lda():
    # Code you'll find on that other website:
    import lda
    from sklearn.feature_extraction.text import CountVectorizer

    # TODO: max_features was initially 10000
    cvectorizer = CountVectorizer( min_df=4, max_features=5000, stop_words='english' )
    abstracts = [ ' '.join( x.words ) for x in docs ]
    cvz = cvectorizer.fit_transform( abstracts )

    n_topics = 20
    n_iter = 2000
    lda_model = lda.LDA( n_topics=n_topics, n_iter=n_iter )
    print( "DONE LDA" )
    X_topics = lda_model.fit_transform( cvz )

    n_top_words = 8
    topic_summaries = []

    topic_word = lda_model.topic_word_
    vocab = cvectorizer.get_feature_names()
    for i, topic_dist in enumerate( topic_word ):
        topic_words = np.array( vocab )[ np.argsort(topic_dist) ][ : -(n_top_words+1):-1 ]
        topic_summaries.append( ' '.join( topic_words ) )
        print( 'Topic {}: {}'.format(i, ' '.join( topic_words) ) )
