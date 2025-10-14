import unittest
from collections import defaultdict

from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

from apps.backend.db import get_connection
from core.models.feed import FeedArticle
from core.pipeline.pipeline import sum_pipeline

class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()

    def test_sum_up(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT f.id, f.title, f.link, f.pub_date, f.summary, fic.content, fgi.feed_group_id
                               FROM feed_items f
                                        LEFT JOIN feed_item_contents fic ON f.id = fic.feed_item_id
                                        JOIN feed_group_items fgi ON f.feed_id = fgi.feed_id
                               WHERE fgi.feed_group_id NOT IN (SELECT group_id
                                                               FROM feed_brief
                                                               WHERE created_at::date = CURRENT_DATE)
                                 AND f.pub_date::date = CURRENT_DATE;

                            """)
                rows = cur.fetchall()
                articles = defaultdict(list)
                for row in rows:
                    group_id = row[6]
                    articles[group_id].append(
                        FeedArticle(
                            id=row[0],
                            title=row[1],
                            url=row[2],
                            content=row[5],
                            pub_date=row[3],
                            summary=row[4],
                            has_full_content=True,
                        )
                    )
                for group, alist in articles.items():
                    report = sum_pipeline(alist)
                    print(f"Group {group} Report:\n{report}\n")
