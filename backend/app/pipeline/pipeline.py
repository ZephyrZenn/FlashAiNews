import logging
from collections import defaultdict

import hdbscan
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

from app.constants import FINAL_REPORT_PROMPT, INDIVIDUAL_SUM_PROMPT, MIN_CLUSTER_SIZE
from app.models.feed import FeedArticle
from app.pipeline.brief_generator import build_generator

generator = build_generator()

logger = logging.getLogger(__name__)
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def sum_pipeline(articles: list[FeedArticle]) -> str:
    individual_summaries = individual_summarization(articles)
    embeddings = embedding(individual_summaries)
    labels = perform_cluster(embeddings)
    grouped = defaultdict(list)  # {cid -> [summary]}
    noise_title = []
    for i, cid in enumerate(labels):
        if cid == -1:  # TODO: Find a better way to deal with noise
            noise_title.append(articles[i].title)
            continue
        grouped[cid].append(individual_summaries[i])
    final_report = []
    for _, sums in grouped.items():
        final_report.append(sum_up(sums))
    noise_part = "Some other topics:\n" + "\n".join(noise_title)
    final_report.append(noise_part)
    return "\n".join(final_report)


def embedding(texts: list[str]) -> np.ndarray:
    embeddings = embedding_model.encode(texts, show_progress_bar=True)
    embeddings = normalize(embeddings, norm="l2")
    return embeddings


def perform_cluster(embeddings: np.ndarray) -> np.ndarray:
    dbscan = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE, metric="euclidean", min_samples=1
    )
    labels = dbscan.fit_predict(embeddings)
    # HDBSCAN can find current hot trends more precisely. But it may need lots of data.
    # In our cases, the amount of data won't be very large. So we just **try** to capture the trends here.
    if np.any(labels != -1):
        return labels
    # If HDBScan can't find a topic, using kmeans as fallback.
    optimal_k = find_optimal_k(embeddings) 
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(embeddings)
    return labels

def find_optimal_k(embeddings: np.ndarray, max_k: int = 5) -> int:
    if len(embeddings) < 2:
        return 1

    scores = {}
    k_range = range(2, min(max_k, len(embeddings)))

    if not k_range:
        return 1

    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
        labels = kmeans.fit_predict(embeddings)
        if len(np.unique(labels)) > 1:
            score = silhouette_score(embeddings, labels)
            scores[k] = score

    if not scores:
        return 1

    return max(scores, key=scores.get)

def individual_summarization(articles: list[FeedArticle]) -> list[str]:
    prompts = [
        INDIVIDUAL_SUM_PROMPT.format(article=article.content) for article in articles
    ]
    summarys = []
    for prompt in prompts:
        summary = generator.completion(prompt)
        summarys.append(summary)
        logger.info(f"Article {id} summarized.")
    return summarys


def sum_up(summaries: list[str]) -> str:
    prompt = FINAL_REPORT_PROMPT.format(summaries=summaries)
    final_report = generator.completion(prompt=prompt)
    return final_report
