from collections import defaultdict

import hdbscan
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize

from app.constants import FINAL_REPORT_PROMPT, INDIVIDUAL_SUM_PROMPT, MIN_CLUSTER_SIZE
from app.models.feed import FeedArticle
from app.pipeline.brief_generator import build_generator

generator = build_generator()


def sum_pipeline(articles: list[FeedArticle]) -> str:
    titles = [article.title for article in articles]
    embeddings = embedding(titles=titles)
    labels = perform_cluster(embeddings, titles)
    individual_summaries = individual_summarization(articles)
    grouped = defaultdict(list)  # {cid -> [summary]}
    noise_title = []
    for i, cid in enumerate(labels):
        if cid == -1:  # TODO: Find a better way to deal with noise
            noise_title.append(articles[i].title)
            continue
        grouped[cid].append(individual_summaries[articles[i].id])
    final_report = []
    for _, sums in grouped.items():
        final_report.append(sum_up(sums))
    noise_part = "Some other topics:\n" + "\n".join(noise_title)
    final_report.append(noise_part)
    return "\n".join(final_report)
     

def embedding(titles: list[str]) -> np.ndarray:
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(titles, show_progress_bar=True)
    embeddings = normalize(embeddings, norm="l2")
    return embeddings


def perform_cluster(embeddings: np.ndarray, titles: list[str]) -> np.ndarray:
    dbscan = hdbscan.HDBSCAN(min_cluster_size=MIN_CLUSTER_SIZE, metric="euclidean")
    labels = dbscan.fit_predict(embeddings)
    return labels


def individual_summarization(articles: list[FeedArticle]) -> dict[str, str]:
    prompts = [
        (article.id, INDIVIDUAL_SUM_PROMPT.format(article=article.content))
        for article in articles
    ]
    summarys = {}
    for id, prompt in prompts:
        summary = generator.completion(prompt)
        summarys[id] = summary
    return summarys


def sum_up(summarys: list[str]) -> str:
    prompt = FINAL_REPORT_PROMPT.format(summarys=summarys)
    final_report = generator.completion(prompt=prompt)
    return final_report
