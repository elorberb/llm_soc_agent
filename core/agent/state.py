from typing import TypedDict, Annotated

from langgraph.graph.message import add_messages, AnyMessage


class AgentState(TypedDict):
    """ State of the agent during a conversation."""
    # Full conversation history
    messages: Annotated[list[AnyMessage], add_messages]
