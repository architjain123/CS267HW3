import math
import heapq
import sys
import os

class Bm25Pruning:
    posting_lists = {}
    num_doc = {}
    doc_lengths = {}
    total_docs = 0

    def __init__(self, words_files):
        self.total_docs = len(words_files)
        doc_num = 1
        for word_list in words_files:
            self.doc_lengths[doc_num] = len(word_list)
            cur_pos = 1
            for word in word_list:
                if word in self.posting_lists:
                    same_doc = False
                    for doc in self.posting_lists[word]:
                        if doc_num == doc[0]:
                            doc[1] += 1
                            doc[2].append(cur_pos)
                            same_doc = True
                            break
                    if not same_doc:
                        self.num_doc[word] += 1
                        self.posting_lists[word].append([doc_num, 1, [cur_pos]])
                else:
                    self.num_doc[word] = 1
                    self.posting_lists[word] = [[doc_num, 1, [cur_pos]]]
                cur_pos += 1
            doc_num += 1

    def tf_bm25(self, term, doc_num):
        k1 = 1.2
        b = 0.75
        l_avg = sum(self.doc_lengths)/len(self.doc_lengths)
        for document in self.posting_lists[term]:
            if document[0] == doc_num:
                return (document[1] * (k1 + 1))/(document[1] + k1 * ((1 - b) + b * (self.doc_lengths[doc_num]/l_avg)))
        return 0

    def get_top_results(self, acc, k):
        h = []
        for result in acc.values():
            if result['docid'] < math.inf:
                heapq.heappush(h, (result['score'], result['docid']))
        return heapq.nlargest(k, h)

    def rankBM25_TermAtATime_WithPruning(self, query_terms, k, a_max, u):
        # max_f is bounded above by a maximum number max_terms of terms allowed in a document.
        # (assume there is some doc length after which we truncate a document to that length)
        max_terms = max(self.doc_lengths.values())

        # sort(t) in increasing order of N[t[i]]
        num_doc_query = []
        for term in query_terms:
            if term in self.num_doc:
                num_doc_query.append(self.num_doc[term])
            else:
                num_doc_query.append(0)
        sorted_num_doc_query = [n for n, q in sorted(zip(num_doc_query, query_terms))]
        sorted_query_terms = [q for n, q in sorted(zip(num_doc_query, query_terms))]

        # initialize accumulators
        acc = {}
        acc_p = {}
        acc[0] = {'docid': math.inf, 'score': math.inf} # end-of-list marker
        for i in range(0, len(sorted_query_terms)):
            if sorted_query_terms[i] not in self.posting_lists:
                continue
            max_f = 0
            quota_left = a_max - len(acc) # the remaining accumulator quota
            if sorted_num_doc_query[i] <= quota_left: # plenty o' accumulators
                # do as we did in rankBM25_TermAtATime
                in_pos = 0 # current pos in acc
                out_pos = 0 # current pos in acc'
                for document in self.posting_lists[sorted_query_terms[i]]:
                    while acc[in_pos]['docid'] < document[0]:
                        # copy previous round to current for docs not containing t[i]
                        acc_p[out_pos] = acc[in_pos].copy()
                        out_pos += 1
                        in_pos += 1
                    acc_p[out_pos] = {'docid': document[0], 'score': math.log(self.total_docs/sorted_num_doc_query[i], 2) * self.tf_bm25(sorted_query_terms[i], document[0])}
                    if acc[in_pos]['docid'] == document[0]:
                        acc_p[out_pos]['score'] += acc[in_pos]['score']
                        in_pos += 1
                    out_pos += 1
            elif quota_left == 0: # no accumulators left
                in_pos = 0 # current pos in acc
                out_pos = 0 # current pos in acc'
                for j in range(0, len(acc)):
                    acc[j]['score'] += math.log(self.total_docs/sorted_num_doc_query[i], 2) * self.tf_bm25(sorted_query_terms[i], acc[j]['docid'])
            else: # still have some accumulators
                tf_stats = [0] * max_terms # initialize TF stats
                t = 1 # init threshold for new accumulators
                postings_seen = 0
                in_pos = 0 # current pos in acc
                out_pos = 0 # current pos in acc'
                for document in self.posting_lists[sorted_query_terms[i]]:
                    while acc[in_pos]['docid'] < document[0]:
                        # copy previous round to current for docs not containing t[i]
                        acc_p[out_pos] = acc[in_pos].copy()
                        out_pos += 1
                        in_pos += 1
                    if acc[in_pos]['docid'] == document[0]:
                        acc_p[out_pos]['docid'] = document[0]
                        acc_p[out_pos]['score'] += acc[in_pos]['score'] + math.log(self.total_docs/sorted_num_doc_query[i], 2) * self.tf_bm25(sorted_query_terms[i], document[0])
                        out_pos += 1
                        in_pos += 1
                    elif quota_left > 0:
                        if document[1] >= t: # if happens, make new accumulator
                            acc_p[out_pos] = {'docid': document[0], 'score': math.log(self.total_docs/sorted_num_doc_query[i], 2) * self.tf_bm25(sorted_query_terms[i], document[0])}
                            out_pos += 1
                            quota_left -= 1
                        tf_stats[document[1]] += 1
                        if document[1] > max_f:
                            max_f = document[1] # update largest observed frequency
                    postings_seen += 1
                    if postings_seen % u == 0:
                        q = (sorted_num_doc_query[i] - postings_seen)/postings_seen
                        j = max_f
                        sum = tf_stats[j] * q
                        while j > 0 and sum < quota_left:
                            j -= 1
                            sum += tf_stats[j] * q
                        t = j
            while acc[in_pos]['docid'] < math.inf: # copy remaining acc to acc'
                acc_p[out_pos] = acc[in_pos].copy()
                out_pos += 1
                in_pos += 1
            acc_p[out_pos] = {'docid': math.inf, 'score': math.inf} # end-of-list marker
            temp = acc
            acc = acc_p
            acc_p = temp
        return self.get_top_results(acc, k) # select using heap

args = sys.argv
words_files = []
for f_name in os.listdir(args[1]):
    if f_name.endswith('.txt'):
        words = []
        with open(args[1] + "/" + f_name, 'r') as file:
            for line in file:
                for word in line.split():
                    words.append(word.lower())
    words_files.append(words)
bm25 = Bm25Pruning(words_files)

query = args[5].split()
top_k = bm25.rankBM25_TermAtATime_WithPruning(query, int(args[2]), int(args[3]), int(args[4]))

for i in range(0, len(top_k)):
    entry = top_k[i]
    print('"' + args[5] + '" 0 ' + str(entry[1]) + " " + str(i + 1) + " " + str(entry[0]) + " " + args[0])
