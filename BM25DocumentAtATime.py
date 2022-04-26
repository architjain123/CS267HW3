import os, sys, math, heapq, re, queue


def get_documents(folder_path):
    documents = []
    total_files_folder = len(os.listdir(folder_path))
    for i in range(1, total_files_folder+1):
        file_name = str(i) + ".txt"
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "r") as file:
            data = file.read()
            data = data.lower()
            data = re.sub(r'[^\w\s]',' ', data)
            data = re.sub(' +', ' ', data)
            documents.append(data)
    return documents


def get_index(documents):
    index = {}
    doc_num = 0
    for document in documents:
        terms = document.split(" ")
        term_num = 0
        for term in terms:
            if term in index:
                index[term].append((doc_num, term_num))
            else:
                index[term] = [(doc_num, term_num)]
            term_num += 1
        doc_num += 1
    return index


def get_term_doc_freq(terms):
    term_doc_freq = []
    term_document_list = {}
    for term in terms:
        posting_list = index[term]
        doc_set = set()
        for doc_id, term_pos in posting_list:
            doc_set.add(doc_id)
        doc_count = len(doc_set)
        term_doc_freq.append((doc_count, term))

        doc_list = sorted(list(doc_set))
        term_document_list[term] = doc_list

    term_doc_freq.sort()
    return term_doc_freq, term_document_list


def tf_bm25(term, doc_id, term_doc_list):

    ftd = 0
    posting_list = index[term]
    for d, term_pos in posting_list:
        if d == doc_id:
            ftd += 1
        elif d > doc_id:
            break

    N = len(documents)
    Nt = len(term_doc_list[term])
    k1 = 1.2
    b = 0.75
    l_d = len(documents[doc_id])
    l_avg_sum = sum(len(document) for document in documents)
    l_avg = l_avg_sum / len(documents)

    idf = math.log(N/Nt)
    tf_bm25 = (ftd * (k1 + 1)) / (ftd + k1 * ((1-b) + b * (l_d/l_avg)))
    return idf * tf_bm25


def get_top_k_results_heaps(acc, k):

    if len(acc) < k:
        k = len(acc)

    heap = []
    for result in acc.values():
        if result['docid'] < math.inf:
            heapq.heappush(heap, (result['score'], result['docid']))
    top_k_results = heapq.nlargest(k, heap)
    return top_k_results


def next_doc(term, doc_id):
    if term in index:
        for d, tpos in index[term]:
            if d > doc_id:
                return d
    return math.inf


def rank_bm25_document_at_a_time(terms, k):

    term_doc_freq, term_doc_list = get_term_doc_freq(terms)

    # result = [score, docid]
    result = queue.PriorityQueue()
    for i in range(k):
        result.put((0, math.inf))

    # terms = [nextDoc, term]
    terms_pq = queue.PriorityQueue()
    for term in terms:
        terms_pq.put((next_doc(term, -math.inf), term))

    while (terms_pq.queue[0][0] < math.inf):
        d = terms_pq.queue[0][0]
        score = 0
        while terms_pq.queue[0][0] == d:
            t = terms_pq.queue[0][1]
            score += tf_bm25(t, d, term_doc_list)
            curr_next_doc, curr_term = terms_pq.get()
            terms_pq.put((next_doc(t, d), curr_term))

        if score > result.queue[0][0]:
            result.get()
            result.put((score, d))


    all_results = []
    while len(result.queue) > 0:
        score, docid = result.get()
        if score != 0:
            all_results.append((score, docid))
    if len(all_results) < k:
        k = len(all_results)

    top_k_results = all_results[-k:]
    top_k_results.reverse()
    return top_k_results


if __name__ == "__main__":

    folder_path = sys.argv[1]
    k = int(sys.argv[2])
    query = sys.argv[3]
    terms = query.split(" ")

    documents = get_documents(folder_path)
    index = get_index(documents)
    top_k_result = rank_bm25_document_at_a_time(terms, k)
    for idx, (score, doc_id) in enumerate(top_k_result):
        print(f"1 0 {doc_id+1} {idx+1} {score} BM_DocumentAtATime")
