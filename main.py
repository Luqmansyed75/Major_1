from dotenv import load_dotenv
load_dotenv()  # Must be first — loads LANGSMITH_* vars before LangChain initializes tracing

import asyncio
import sys
import uuid

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from config.logger_config import logger

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"


async def main():
    print("=" * 60)
    print("  Live Rag - Eval: Interactive Agent Assistant (with HITL)")
    print("=" * 60)
    print("Type your question below (or type 'exit' / 'q' to quit).\n")

    # Load tools and graph builder
    from client.mcp_client import load_all_tools_async
    from agent.graph import build_graph

    # PostgreSQL integrations (async versions required for ainvoke/astream)
    from langgraph.store.postgres.aio import AsyncPostgresStore
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    print("Loading MCP tools...")
    tools = await load_all_tools_async()

    # ---------------------------------------------------------
    # AsyncPostgresStore + AsyncPostgresSaver
    # ---------------------------------------------------------
    #
    # AsyncPostgresStore:
    #   Used for long-term memory / application data.
    #
    # AsyncPostgresSaver:
    #   Used for LangGraph checkpoints / thread state.
    #
    # Async versions are required because graph.ainvoke() calls
    # async checkpoint methods (aget_tuple, aput, etc.).
    # Both connections are kept alive for the entire session.
    # ---------------------------------------------------------

    async with AsyncPostgresStore.from_conn_string(DB_URI) as store:
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:

            # Create required PostgreSQL tables
            await store.setup()
            await checkpointer.setup()

            # -------------------------------------------------
            # Build and COMPILE the graph
            # -------------------------------------------------
            #
            # IMPORTANT:
            # The checkpointer must be passed into build_graph
            # BEFORE the graph is compiled.
            # -------------------------------------------------

            graph = build_graph(
                tools=tools,
                store=store,
                checkpointer=checkpointer,
            )

            print(f"Graph ready with {len(tools)} tools.\n")

            # # Each conversation gets its own thread
            # thread_id = str(uuid.uuid4())

            config = {
                "configurable": {
                    "thread_id": "thread_id_2",
                    "user_id": "u2",
                },
                "run_name": "live-rag-eval-agent",  # Trace name shown in LangSmith UI
                "metadata": {                        # Visible as key-value in LangSmith
                    "project": "Live_rag_eval",
                    "env": "development",
                },
            }

            # -------------------------------------------------
            # Interactive conversation loop
            # -------------------------------------------------

            while True:
                try:
                    user_input = input("\nYou: ").strip()

                    if not user_input:
                        continue

                    if user_input.lower() in ("exit", "quit", "q"):
                        print("Goodbye!")
                        break

                    print("\nAgent thinking...", flush=True)

                    result = await graph.ainvoke(
                        {
                            "messages": [
                                HumanMessage(content=user_input)
                            ]
                        },
                        config=config,
                    )

                    # -------------------------------------------------
                    # HITL handling
                    # -------------------------------------------------

                    while True:

                        # Because the graph has a checkpointer,
                        # this state can be recovered using thread_id.
                        state = await graph.aget_state(config)

                        # No pending interrupts
                        if not state.tasks or not any(
                            task.interrupts for task in state.tasks
                        ):
                            break

                        for task in state.tasks:
                            for intr in task.interrupts:

                                data = intr.value

                                tool_name = data.get(
                                    "tool_name",
                                    "unknown",
                                )

                                args = data.get(
                                    "args",
                                    {},
                                )

                                print("\n" + "=" * 60)
                                print(
                                    f"  [HITL REVIEW] "
                                    f"High-risk action: '{tool_name}'"
                                )
                                print("=" * 60)

                                for key, value in args.items():
                                    print(f"  {key}: {value}")

                                print("-" * 60)

                                decision = input(
                                    "  Approve this action? (yes/no): "
                                ).strip()

                                # Resume the interrupted graph
                                result = await graph.ainvoke(
                                    Command(resume=decision),
                                    config=config,
                                )

                    # -------------------------------------------------
                    # Print final response
                    # -------------------------------------------------

                    final_msg = result["messages"][-1]

                    if hasattr(final_msg, "content") and final_msg.content:
                        print(
                            f"\nAssistant:\n"
                            f"{final_msg.content}\n"
                        )

                    print("-" * 60)

                except KeyboardInterrupt:
                    print("\nSession interrupted. Goodbye!")
                    break

                except Exception as e:
                    logger.error(f"Error during conversation: {repr(e)}", exc_info=True)
                    print(f"\nError: {repr(e)}\n")


if __name__ == "__main__":
    import selectors
    # psycopg async requires SelectorEventLoop on Windows
    # (default ProactorEventLoop is incompatible)
    asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
