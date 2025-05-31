import math
from collections import Counter, defaultdict

import numpy as np


def build_index(records):
    all_keys = set()
    for r in records:
        all_keys.update(r.keys())

    def stringify(record):
        return ", ".join(str(record.get(k, "")) for k in sorted(all_keys))

    texts = [stringify(r) for r in records]
    tf_list = compute_tf(texts)
    idf = compute_idf(texts)
    tfidf_matrix, vocab = compute_tfidf(tf_list, idf)

    return tfidf_matrix, idf, vocab, texts


def search(query, idf, vocab, tfidf_matrix):
    words = query.lower().split()
    tf = Counter(words)
    total = sum(tf.values())
    tf = {w: tf[w] / total for w in tf}

    query_vector = [tf.get(word, 0) * idf.get(word, 0) for word in vocab]

    similarities = cosine_similarity(query_vector, tfidf_matrix)
    ranked_indices = np.argsort(similarities)[::-1]
    return similarities, ranked_indices


def compute_tf(texts):
    tf_list = []
    for text in texts:
        words = text.lower().split()
        counter = Counter(words)
        total = sum(counter.values())
        tf = {word: count / total for word, count in counter.items()}
        tf_list.append(tf)
    return tf_list


def compute_idf(texts):
    N = len(texts)
    df = defaultdict(int)
    for text in texts:
        words = set(text.lower().split())
        for word in words:
            df[word] += 1
    idf = {word: math.log(N / (df[word])) for word in df}
    return idf


def compute_tfidf(tf_list, idf):
    tfidf_matrix = []
    vocab = sorted(idf.keys())
    for tf in tf_list:
        vector = [tf.get(word, 0) * idf[word] for word in vocab]
        tfidf_matrix.append(vector)
    return tfidf_matrix, vocab


def cosine_similarity(query_vector, doc_matrix):
    similarities = []
    for doc_vector in doc_matrix:
        dot = np.dot(query_vector, doc_vector)
        norm_query = np.linalg.norm(query_vector)
        norm_doc = np.linalg.norm(doc_vector)
        sim = dot / (norm_query * norm_doc) if norm_query and norm_doc else 0.0
        similarities.append(sim)
    return similarities
