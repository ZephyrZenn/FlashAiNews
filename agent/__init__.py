import logging
from typing import Optional
from agent.tools import create_default_toolbox
from agent.workflow import SummarizeAgenticWorkflow
from agent.tools.filter_tool import KeywordExtractorTool
from agent.boost_agent import BoostAgent
from core.brief_generator import build_generator, APIKeyNotConfiguredError

logger = logging.getLogger(__name__)





# 单例实例
_agent_instance: Optional[SummarizeAgenticWorkflow] = None
_boost_agent_instance: Optional[BoostAgent] = None


def init_agent() -> SummarizeAgenticWorkflow:
    """应用启动时调用，初始化 Agent 单例。
    
    Uses lazy initialization so the app can start without API keys configured.
    API key errors will only occur when actually using the agent.
    """
    global _agent_instance
    if _agent_instance is None:
        # Use lazy_init=True to allow app to start without API key
        _agent_instance = SummarizeAgenticWorkflow(lazy_init=True)
        logger.info("Agent initialized (lazy mode - API key checked on first use)")
    return _agent_instance


def get_agent() -> SummarizeAgenticWorkflow:
    """获取 Agent 单例实例。
    
    Raises:
        RuntimeError: If agent is not initialized.
        APIKeyNotConfiguredError: When summarize() is called without API key configured.
    """
    if _agent_instance is None:
        raise RuntimeError("Agent 未初始化，请先调用 init_agent()")
    return _agent_instance


def init_boost_agent() -> Optional[BoostAgent]:
    """初始化 Function Calling Agent 单例。
    
    Uses lazy initialization so the app can start without API keys configured.
    API key errors will only occur when actually using the agent.
    
    Returns:
        FlexibleFunctionCallAgent 实例，如果 API key 未配置则返回 None
    """
    global _boost_agent_instance
    if _boost_agent_instance is None:
        try:
            client = build_generator()
            toolbox = create_default_toolbox()
            # 注册需要 client 的工具
            keyword_tool = KeywordExtractorTool(client)
            toolbox.register(keyword_tool, tags=["analysis", "llm"])
            _boost_agent_instance = BoostAgent(client, toolbox)
            logger.info("Flexible Function Calling Agent initialized (lazy mode)")
        except APIKeyNotConfiguredError:
            # 延迟初始化，允许应用启动时没有 API key
            logger.info("Flexible Agent will be initialized on first use (API key not configured)")
            return None
    return _boost_agent_instance


def get_boost_agent() -> BoostAgent:
    """获取 Function Calling Agent 单例实例。
    
    Raises:
        RuntimeError: If agent is not initialized and API key is not configured.
        APIKeyNotConfiguredError: When API key is not configured.
    """
    global _boost_agent_instance
    if _boost_agent_instance is None:
        # 尝试初始化
        agent = init_boost_agent()
        if agent is None:
            # API key 未配置，尝试再次初始化以触发异常
            try:
                client = build_generator()
                toolbox = create_default_toolbox()
                keyword_tool = KeywordExtractorTool(client)
                toolbox.register(keyword_tool, tags=["analysis", "llm"])
                _boost_agent_instance = BoostAgent(client, toolbox)
            except APIKeyNotConfiguredError as e:
                raise RuntimeError(
                    "Boost Agent 未初始化且 API key 未配置，请先配置 API key"
                ) from e
    return _boost_agent_instance
