import asyncio
from backend.Jarvis_productivity import add_todo, get_todo_list, delete_todo_item, set_alarm

async def test_productivity():
    print("Testing To-Do List...")
    print(await add_todo("Test Task 1"))
    print(await add_todo("Test Task 2"))
    print(await get_todo_list())
    print(await delete_todo_item(1))
    print(await get_todo_list())

    print("\nTesting Alarm (5 seconds)...")
    print(await set_alarm(5, "Test Alarm"))
    print("Waiting for alarm...")
    await asyncio.sleep(6)
    print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_productivity())
