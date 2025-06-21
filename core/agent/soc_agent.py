import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

from core.agent.state import AgentState

load_dotenv()


class SocAgent:
    """
    A SOC Agent that interacts with a database manager to handle incident cases.
    """

    def __init__(self, db_manager=None):
        self.llm = self._init_llm()
        self.manager = db_manager
        # insert all the methods from the manager as tools without the "save" method and private methods
        self.tools = [
            getattr(self.manager, attr)
            for attr in dir(self.manager)
            if not attr.startswith("_")  # Exclude private/internal methods
               and callable(getattr(self.manager, attr))  # Only keep methods
               and attr not in {"save"}  # Exclude specific methods if needed
        ]
        self.graph = self._build_graph()

    @staticmethod
    def _init_llm():
        """ Initialize the LLM with Azure OpenAI settings."""
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            temperature=0,
        )

    @staticmethod
    def _build_prompt():
        """ Build the chat prompt template for the SOC Agent."""
        return ChatPromptTemplate.from_messages([
            ("system",
             "You are a SOC assistant that helps manage incident cases.\n"
             "You can use tools to list notes, add/remove/edit them, change status or severity.\n"
             "Use a tool if it can help. Do not guess — prefer tools."),
            ("placeholder", "{messages}")
        ])

    @staticmethod
    def _handle_tool_error(state: AgentState):
        """ Handle tool errors by returning a message with the error details."""
        err = state.get("error")
        tool_calls = state["messages"][-1].tool_calls
        return {
            "messages": [
                ToolMessage(
                    content=f"Tool error: {err!r}. Please fix.",
                    tool_call_id=call["id"]
                ) for call in tool_calls
            ]
        }

    def _create_tool_node(self, tools: list) -> dict:
        """
        Function to create a tool node with fallback error handling.
        """
        return ToolNode(tools).with_fallbacks(
            [RunnableLambda(self._handle_tool_error)],  # Use a lambda function to wrap the error handler
            exception_key="error"  # Specify that this fallback is for handling errors
        )

    @staticmethod
    def _create_assistant_node(llm_chain):
        """ Create an assistant node that invokes the LLM chain and handles tool calls."""

        def assistant_node(state: AgentState):
            """ Invoke the LLM chain and handle tool calls."""
            while True:
                result = llm_chain.invoke(state)
                if not result.tool_calls and (
                        not result.content or
                        (isinstance(result.content, list) and not result.content[0].get("text"))
                ):
                    state["messages"].append(HumanMessage(content="Respond with a real output."))
                else:
                    break
            return {"messages": result}

        return assistant_node

    def _build_graph(self):
        """ Build the state graph for the SOC Agent."""
        prompt = self._build_prompt()
        llm_chain = prompt | self.llm.bind_tools(self.tools)

        # tool node (unchanged, but already returns {"messages": [...]})
        tool_node = self._create_tool_node(self.tools)

        # Build graph
        builder = StateGraph(AgentState)
        builder.add_node("assistant", self._create_assistant_node(llm_chain))
        builder.add_node("tools", tool_node)

        builder.add_edge(START, "assistant")  # first turn
        builder.add_conditional_edges("assistant", tools_condition)
        builder.add_edge("tools", "assistant")  # loop after tool
        builder.set_entry_point("assistant")

        memory = MemorySaver()
        return builder.compile(checkpointer=memory)
