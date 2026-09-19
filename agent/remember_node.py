"""This is used for ltm and this node decide weahter there is something important to store in the memory"""
from dotenv import load_dotenv
load_dotenv()

import uuid
from typing import List
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.store.base import BaseStore
from langgraph.types import Command
from config.logger_config import logger
#----------------------------------------------------------------------------
MEMORY_PROMPT = """You are responsible for updating and maintaining accurate user memory.

CURRENT USER DETAILS (existing memories):
{user_details_content}

TASK:
- Review the user's latest message.
- Extract user-specific info worth storing long-term (identity, stable preferences, ongoing projects/goals).
- For each extracted item, set is_new=true ONLY if it adds NEW information compared to CURRENT USER DETAILS.
- If it is basically the same meaning as something already present, set is_new=false.
- Keep each memory as a short atomic sentence.
- No speculation; only facts stated by the user.
- If there is nothing memory-worthy, return an empty list.
"""
#-------------------------------------------------------------------
import os
memory_llm=ChatGroq(model=os.getenv("GROQ_MODEL"), temperature=0)
logger.info(f"Memory LLM initialized with model: {os.getenv('GROQ_MODEL')}")
#----------------------------------------------------------------
class MemoryItem(BaseModel):
    text: str = Field(description="Atomic user memory")
    is_new: bool = Field(description="True if new, false if duplicate")
class MemoryDecision(BaseModel):
    should_write: bool
    memories: List[MemoryItem] = Field(default_factory=list, description="Atomic user memories to store")

memory_extractor = memory_llm.with_structured_output(MemoryDecision)


async def chat_creates_memory_node(state: MessagesState, config: RunnableConfig, store: BaseStore):
    logger.info("remember_node | entered")

    user_id = config["configurable"]["user_id"]

    namespace = ("user", user_id, "details")

    # A) Load existing memories
    existing_items = await store.asearch(namespace)
    existing_texts = [it.value.get("data", "") for it in existing_items if it.value.get("data")]
    user_details_content = "\n".join(f"- {t}" for t in existing_texts) if existing_texts else "(empty)"

    # B) Latest user message — extract plain text, not the full message object
    last_text = state["messages"][-1].content
    

    # C) LLM extracts memories + marks new vs duplicate
    decision: MemoryDecision = await memory_extractor.ainvoke(
        [
            SystemMessage(content=MEMORY_PROMPT.format(user_details_content=user_details_content)),
            {"role": "user", "content": f"USER MESSAGE:\n{last_text}"},
        ]
    )

    # D) Store ONLY new memories
    if decision.should_write:
        for mem in decision.memories:
                if mem.is_new:
                    await store.aput(namespace, str(uuid.uuid4()), {"data": mem.text})
                    logger.info(f"Stored new memory for user {user_id}: {mem.text}")

    return Command(
            goto="agent"
        )



