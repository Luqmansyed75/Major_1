import asyncio
import sys
import uuid
from langchain_core.messages import HumanMessage
from langgraph.types import Command

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


async def main():
    print("=" * 60)
    print("  Live Rag - Eval: Interactive Agent Assistant (with HITL)")
    print("=" * 60)
    print("Type your question below (or type 'exit' / 'q' to quit).\n")

    # Load tools and build graph (sync is fine here - no running loop yet)
    from client import load_all_tools_async
    from agent.graph import build_graph
    print("Loading MCP tools...")
    tools = await load_all_tools_async()
    graph = build_graph(tools)
    print(f"Graph ready with {len(tools)} tools.\n")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

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
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            )

            while True:
                state = await graph.aget_state(config)

                if not state.tasks or not any(task.interrupts for task in state.tasks):
                    break

                for task in state.tasks:
                    for intr in task.interrupts:
                        data = intr.value
                        tool_name = data.get("tool_name", "unknown")
                        args = data.get("args", {})

                        print("\n" + "=" * 60)
                        print(f"  [HITL REVIEW] High-risk action: '{tool_name}'")
                        print("=" * 60)
                        for key, value in args.items():
                            print(f"  {key}: {value}")
                        print("-" * 60)

                        decision = input("  Approve this action? (yes/no): ").strip()

                result = await graph.ainvoke(
                    Command(resume=decision),
                    config=config,
                )

            final_msg = result["messages"][-1]
            if hasattr(final_msg, "content") and final_msg.content:
                print(f"\nAssistant:\n{final_msg.content}\n")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())