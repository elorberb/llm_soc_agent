import asyncio
import uuid
from typing import AsyncIterable

import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage

from core.agent.soc_agent import SocAgent  # make sure this path is correct
from core.db_manager import DBManager  # make sure this path is correct

manager = DBManager("db.json")
agent = SocAgent(db_manager=manager)


@cl.on_chat_start
def start_chat():
    thread_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id)


async def get_response(user_input: str) -> AsyncIterable[str]:
    thread_id = cl.user_session.get("thread_id")
    config = {"configurable": {"thread_id": thread_id}}

    stream = agent.graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="values"
    )

    final_ai_msg = None

    for step in stream:
        for msg in step.get("messages", []):
            if isinstance(msg, AIMessage):
                final_ai_msg = msg  # override previous one

    # Yield only the final assistant message
    if final_ai_msg:
        yield final_ai_msg.content
        await asyncio.sleep(0)

    manager.save()


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")

    async for token in get_response(message.content):
        await msg.stream_token(token)

    await msg.update()
