import unittest
from collections import defaultdict

from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

from app.db import get_connection
from app.models.feed import FeedArticle
from app.pipeline.pipeline import sum_pipeline

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

    def test_embed_similarity(self):
        titles = ['U.S. government takes stake in Canadian lithium miner and its Nevada mining project', 'Meta 发布新模型 CWM，助力代码理解与生成', '​前 OpenAI 与 DeepMind 研究者获 3 亿美元种子融资，力图实现科学自动化', '​特朗普签署命令投资5000万美元助力儿童癌症人工智能研究', '英伟达市值突破 4.5 万亿美元，AI 基础设施交易频频达成', 'Opera 推出 AI 驱动的 Neon 浏览器，助力高效工作与智能任务管理', 'OpenAI 推出 Sora 短视频应用，升级视频生成模型 Sora 2']
        from app.pipeline.pipeline import embedding, perform_cluster
        embs = embedding(titles)
        sim = cosine_similarity(embs)
        df = pd.DataFrame(sim)
        print(df)