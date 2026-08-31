import asyncio
import json
import sys
import uuid
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agent.graph import graph

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

            # Run the graph — may pause at an interrupt
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            )

            # Check if the graph paused at an HITL interrupt
            while True:
                state = await graph.aget_state(config)

                # If no pending interrupts, we're done
                if not state.tasks or not any(
                    task.interrupts for task in state.tasks
                ):
                    break

                # Process each interrupt (high-risk tool approval)
                for task in state.tasks:
                    for intr in task.interrupts:
                        data = intr.value
                        tool_name = data.get("tool_name", "unknown")
                        args = data.get("args", {})

                        # Display the proposed action to the user
                        print("\n" + "=" * 60)
                        print(f"  [HITL REVIEW] High-risk action: '{tool_name}'")
                        print("=" * 60)
                        for key, value in args.items(): 
                            print(f"  {key}: {value}")
                        print("-" * 60)

                        decision = input("  Approve this action? (yes/no): ").strip()

                # Resume the graph with the user's decision
                result = await graph.ainvoke(
                    Command(resume=decision),
                    config=config,
                )

            # Print the final agent response
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
