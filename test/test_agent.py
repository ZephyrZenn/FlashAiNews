

import asyncio
import os
import unittest
from dotenv import load_dotenv

from agent import SummarizeAgent
from core.config.loader import load_config


class AgentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global cfg
        # Ensure environment variables are loaded
        load_dotenv()
        # Verify required environment variables
        required_vars = [
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_HOST",
            "POSTGRES_DB",
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        cfg = load_config()
        
    def test_agent(self):
        agent = SummarizeAgent()
        # 边执行边输出的回调函数
        def on_step(message: str):
            print(f"[STEP] {message}")
        
        result = asyncio.run(agent.summarize(48, [1, 2], on_step=on_step))
        print("\n=== 最终结果 ===")
        print(result)