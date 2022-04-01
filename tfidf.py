import numpy as np
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# vectorizer = TfidfVectorizer()
# vectors = vectorizer.fit_transform(["what is my ip", "my ip has been provided"])
# feature_names = vectorizer.get_feature_names()
# dense = vectors.todense()
# denselist = dense.tolist()
# df = pd.DataFrame(denselist, columns=feature_names)

# print(cosine_similarity(dense[0], dense[1]))



import math 
from numpy import dot
from numpy.linalg import norm

scores = {}

def calc_tf(vec):
    uq_words = {}
    st = vec.split()
    for word in st:
        if word in uq_words.keys(): uq_words[word] += 1
        else: uq_words[word] = 1
    for term in uq_words: uq_words[term] = math.log2(uq_words[term]) + 1
    return uq_words

def find_occ(term, tfs):
    count = 0
    for vec in tfs:
        if term in tfs[vec].keys(): count += 1
    return count

def calc_idfs(tfs):
    idfs = {}
    for vec in tfs:
        for term in tfs[vec]:
            idfs[term] = math.log2(51/find_occ(term, tfs))  
    return idfs

def calc_tfidfs(tfs, idfs):
    tf_idfs = {}
    for vec in tfs:
        tf_idfs[vec] = {}
        for term in tfs[vec]:
            tf_idfs[vec][term] = tfs[vec][term] * idfs[term]
    return tf_idfs

def comp_vec_sim(q, d, num):
    # print(q, d)
    q_vec = []
    d_vec = []
    for term in q:
        q_vec.append(q[term])
        if term not in d.keys(): d_vec.append(0)
        else: d_vec.append(d[term]) 
    for term in d:
        if term in q.keys(): continue
        d_vec.append(d[term])
        q_vec.append(0)
    
    score = round(dot(q_vec, d_vec)/(norm(q_vec)*norm(d_vec)), 3)
    if score > 0 : scores[num] = score

def calc_sim(tf_idfs):
    sim = {}
    for i, doc in enumerate(tf_idfs):
        if doc == "query": continue
        sim[doc] = comp_vec_sim(tf_idfs["query"], tf_idfs[doc], i)

    return sim

def write_res(filename):
    out = open(filename, "w")
    sorted_tuples = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    for k,v in sorted_tuples:
        out.write(str(k)+": "+str(v)+"\n")
    out.close()


def write_to_file(content, filename):
    with open(filename, "w") as f:
        f.write(content)


count = 0
with open("queries.txt", "r") as f:
    lines = f.readlines()
    for query in lines:
        tfs = {}
        tfs["query"] = calc_tf(query)
        docs = []
        i = 0
        for file in os.listdir("temp"):
            with open(os.path.join("temp", file),"r") as f:
                data = f.read()
                docs.append(data)
                tfs["d"+str(i)] = calc_tf(data)
                i+=1

        idfs = calc_idfs(tfs)
        tf_idfs = calc_tfidfs(tfs, idfs)
        write_to_file(str(tf_idfs), f"incorrect/tfidf{count}.txt")
        calc_sim(tf_idfs)
        write_res(f"incorrect/output{count}.txt")
        count +=1