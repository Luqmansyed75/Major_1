from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State schema holding message history with the add_messages reducer."""
    messages: Annotated[list[BaseMessage], add_messages]
