import asyncio
import sys
import uuid
from langchain_core.messages import HumanMessage
from agent.graph import graph

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


async def main():
    print("=" * 60)
    print("       Live Rag - Eval: Interactive Agent Assistant       ")
    print("=" * 60)
    print("Type your question below (or type 'exit' or 'q' to quit).\n")

    # Unique thread ID for this conversation session (memory retention)
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

            agent_response = result["messages"][-1].content
            print(f"\nAssistant:\n{agent_response}\n")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())

