# -*- coding: utf-8 -*-

from __future__ import division
import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import re
import pickle
import pymysql.cursors
import numpy as np
import math
import operator

# mysql connection
conn = pymysql.connect(host="localhost",
                       user="root",
                       passwd="root",
                       db="python")
x = conn.cursor()
#Choose table in database
sql = "SELECT * FROM python.tweetsmining" 
All_Tweets = []
try:
   # Execute the SQL command
   x.execute(sql)
   # Fetch all the rows in a list of lists.
   Tweets = x.fetchall()
   for row in Tweets:
       rows = {}
       rows["fid"]          = row[0]
       rows["text"]         = row[1]
       rows["date"]         = row[2]
       rows["sentiment"]    = row[3]
       rows["parkname"]     = row[4]
       rows["location"]     = row[5]
       rows["keyword"]      = row[6]
       All_Tweets.append(rows)
   print("success: database have been imported")
except:
   print("Error: unable to fecth data")
# disconnect from server
conn.close()

# Sum of Different word
tokenize = lambda doc: doc.lower().split(" ")

## Functions
"-----------------------------------------------------------------------------"
def jaccard_similarity(query, document):
    intersection = set(query).intersection(set(document))
    union = set(query).union(set(document))
    return len(intersection)/len(union)

def term_frequency(term, tokenized_document):
    return tokenized_document.count(term)

def sublinear_term_frequency(term, tokenized_document):
    count = tokenized_document.count(term)
    if count == 0:
        return 0
    return 1 + math.log(count)

def augmented_term_frequency(term, tokenized_document):
    max_count = max([term_frequency(t, tokenized_document) for t in tokenized_document])
    return (0.5 + ((0.5 * term_frequency(term, tokenized_document))/max_count))

def inverse_document_frequencies(tokenized_documents):
    idf_values = {}
    all_tokens_set = set([item for sublist in tokenized_documents for item in sublist])
    for tkn in all_tokens_set:
        contains_token = map(lambda doc: tkn in doc, tokenized_documents)
        idf_values[tkn] = 1 + math.log(len(tokenized_documents)/(sum(contains_token)))
    return idf_values

def tfidf(documents):
    # Count text positive and negative
    Txpos = 0; Txneg = 0; TxDocpos = []; TxDocneg = [];
    for twee in documents:
        if (twee["sentiment"]==1):
            Txpos = Txpos + 1;
            TxDocpos.append(twee["text"]);
        else:
            Txneg = Txneg + 1;
            TxDocneg.append(twee["text"]);
    # Prosentase
    SumSent = Txpos + Txneg;
    Txpos = Txpos/SumSent; Txneg = Txneg/SumSent; 
    Tsentiment = []; Tsentiment.append(TxDocneg); Tsentiment.append(TxDocpos);
    # Separate sentiment Documents
    ResultsSent = []
    for i in range (len(Tsentiment)):
        if (i == 0):
            Prosentage = Txneg;
        else:
            Prosentage = Txpos;
        tokenized_documents = [tokenize(d) for d in Tsentiment[i]]
        idf = inverse_document_frequencies(tokenized_documents)
        allres= []
        tfidf_documents = []
        tfidf_documents2 = []
        for document in tokenized_documents:
            doc_tfidf = []
            doc_tfidf2 = {}
            for term in idf.keys():
                tf = sublinear_term_frequency(term, document)
                doc_tfidf.append(tf * idf[term] * Prosentage)
                doc_tfidf2[term] = (tf * idf[term] * Prosentage)
            tfidf_documents.append(doc_tfidf)
            tfidf_documents2.append(doc_tfidf2)
        allres.append(tfidf_documents)
        allres.append(tfidf_documents2)
        ResultsSent.append(allres);
    return ResultsSent

def cosine_similarity(vector1, vector2):
    dot_product = sum(p*q for p,q in zip(vector1, vector2))
    magnitude = math.sqrt(sum([val**2 for val in vector1])) * math.sqrt(sum([val**2 for val in vector2]))
    if not magnitude:
        return 0
    return dot_product/magnitude
"-----------------------------------------------------------------------------"

## HINTS 
global Activity, Keyactivity
Activity = {'workout': ['workout', 'running', 'walking', 'run', 'parkrun', 'jog', 'jogging', 'walk', 'walking', 'ride','cycling'],
  'socializing': ['relax', 'relaxing', 'meditation', 'reading', 'lunch', 'chill', 'mindfulness', 'yoga'],
  'relaxation': ['meetup', 'wedding', 'bbq', 'picnic', 'catchup', 'friends', 'festival', 'hangout', 'party','birthday']}
Keyactivity = ['workout','socializing','relaxation'];
#_Coding_below_here____________________________________________________________

# Filter based on Location
Tweet_Locations = {}
global Locations
Locations = ['Central Park','Bronx Park','Van Cortlandt Park'];
for loc in Locations:
    loca = [];
    for item in All_Tweets:
        if (item["parkname"].find(loc)) != -1:
            loca.append(item);
    Tweet_Locations[loc] = loca;

global ParkRecAct
ParkRecAct = {};
# Recomendation
for mykey in Keyactivity:
    ParkRec = {};
    prefer = Activity[mykey];
    for Twee in Locations:
        if (bool((Tweet_Locations.get(Twee))) == True):
            tfidf_representation = tfidf(Tweet_Locations[Twee]);
            MyreccA = []; 
            for sent in range (len(tfidf_representation)):
                Act = {};
                for i in range (len(prefer)):
                    if (prefer[i]):
                        TextF = tfidf_representation[sent][1]; # Means = only positive
                        CountT = 0;
                        for j in range (len(TextF)):
                            Kt = TextF[j];
                            if (bool(Kt.get(prefer[i])) == True):
                                CountT = CountT + Kt[prefer[i]];
                            Act[prefer[i]] = CountT;
                MyreccA.append(Act);
            ParkRec[Twee]=MyreccA;
        if (bool((Tweet_Locations.get(Twee))) == False):
            ParkRec[Twee]=[];
    ParkRecAct[mykey] = ParkRec;
print("Classification: Classification and Recommendation finish")

#Give recommendation
def IwantTo(Input):
    # example (Input = Run)
    global ParkRecAct,Activity,Keyactivity,Locations
    for item in Keyactivity:
        A = Activity[item]
        for B in A:
            if (bool(B == Input)==True):
                Note = item;
    Recc = ParkRecAct[Note]
    accset = Activity[Note]
    LocRec = {}; SortLocRec = {};
    for lcc in Locations:
        dat = [];
        Subtract = {};
        Loc = Recc[lcc]
        for aac in accset:
            dat.append(abs(Loc[1][aac]-Loc[0][aac]));
        mxx = max(dat); mnn = min(dat);
        for aac in accset:
            Subtract[aac] = ((abs(Loc[1][aac]-Loc[0][aac])-mnn)/(mxx-mnn))*(90);
        LocRec[lcc] = Subtract;
        SortLocRec[lcc] = sorted(Subtract.items(), key=operator.itemgetter(1),reverse=True);
    
    return SortLocRec
MyPreference = IwantTo('what activity do you want?')


#Workout = IwantTo('run')
#Socializing = IwantTo('relax')
#Relaxation = IwantTo('meetup')


## Export to database
## mysql connection
#conn = pymysql.connect(host="localhost",
#                       user="root",
#                       passwd="root",
#                       db="python")
#
#
### Prepare SQL query to INSERT a record into the database.
##sql = """INSERT INTO python.RECOMENDATION(FIRST_NAME,
##         LAST_NAME, AGE, SEX, INCOME)
##         VALUES ('Mac', 'Mohan', 20, 'M', 2000)"""
#try:
#    # prepare a cursor object using cursor() method
#    cursor = conn.cursor()
#    # SQL query string
#    sqlQuery = "CREATE TABLE RECOMMENDATION(id int, Parkname varchar(32), Activity varchar(32), Value float)"    
#    # Execute the SQL command
#    cursor.execute(sql)
#    # SQL query string
#    sqlQuery = "show tables"
#    # Execute the sqlQuery
#    cursor.execute(sqlQuery)
#    # Commit your changes in the database
#    conn.commit()
#except:
#    # Rollback in case there is any error
#    conn.rollback()
#
## disconnect from server
#conn.close()

