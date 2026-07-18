import csv
import os
import re
from collections import Counter
from math import log


class BM25KeywordIndex:
    """A lightweight BM25 implementation for keyword retrieval over text chunks."""

    def __init__(self, documents, k1=1.5, b=0.75):
        self.documents = list(documents)
        self.k1 = k1
        self.b = b
        self.doc_ids = []
        self.doc_texts = []
        self.doc_lengths = []
        self.doc_freqs = Counter()
        self.idf_cache = {}
        self.avgdl = 0.0

        for index, doc in enumerate(self.documents):
            doc_id = doc.get("id") or str(index)
            text = doc.get("text") or doc.get("content") or ""
            tokens = self._tokenize(text)
            self.doc_ids.append(doc_id)
            self.doc_texts.append(text)
            self.doc_lengths.append(len(tokens))
            self.doc_freqs.update(set(tokens))

        if self.doc_lengths:
            self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths)

    @classmethod
    def from_documents(cls, documents, **kwargs):
        return cls(documents=documents, **kwargs)

    @classmethod
    def from_chunk_index(cls, index_path, chunks_dir, **kwargs):
        documents = []
        if not os.path.exists(index_path):
            return cls(documents=documents, **kwargs)

        with open(index_path, "r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                chunk_filename = row.get("chunk_filename", "")
                chunk_path = os.path.join(chunks_dir, chunk_filename)
                if not os.path.exists(chunk_path):
                    continue

                with open(chunk_path, "r", encoding="utf-8") as chunk_file:
                    text = chunk_file.read()

                documents.append(
                    {
                        "id": chunk_filename.replace(".txt", ""),
                        "text": text,
                        "metadata": {
                            "act_name": row.get("act_name", "Unknown"),
                            "section_article_number": row.get("section_article_number", "Unknown"),
                            "chunk_id": row.get("chunk_id"),
                            "word_count": row.get("word_count"),
                        },
                    }
                )

        return cls(documents=documents, **kwargs)

    def _tokenize(self, text):
        return re.findall(r"\b[a-z0-9]+\b", text.lower())

    def _idf(self, term):
        if term in self.idf_cache:
            return self.idf_cache[term]

        doc_freq = self.doc_freqs.get(term, 0)
        if doc_freq == 0:
            self.idf_cache[term] = 0.0
            return 0.0

        n_docs = len(self.documents)
        idf = log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
        self.idf_cache[term] = idf
        return idf

    def search(self, query, top_k=5):
        if not self.documents:
            return []

        query_terms = [term for term in self._tokenize(query) if term]
        if not query_terms:
            return []

        valid_terms = [term for term in query_terms if self._idf(term) > 0]
        if not valid_terms:
            return []

        results = []
        for idx, text in enumerate(self.doc_texts):
            token_counts = Counter(self._tokenize(text))
            score = 0.0
            for term in valid_terms:
                tf = token_counts.get(term, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[idx]
                denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl if self.avgdl else 0))
                score += self._idf(term) * ((tf * (self.k1 + 1)) / denom)

            if score > 0:
                results.append(
                    {
                        "id": self.doc_ids[idx],
                        "text": text,
                        "score": round(score, 6),
                        "metadata": self.documents[idx].get("metadata", {}),
                    }
                )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]
