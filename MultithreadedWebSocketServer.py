import asyncio
from websockets.server import serve
import threading
from threading import Event
import time

clients = set()
TASK_QUE = {}


async def register(websocket, path):
    clients.add(websocket)


async def unregister(websocket, path):
    if len(clients) > 0:
        clients.remove(websocket)


async def Task(ws, taskId, event: Event):
    for i in range(0, 100):
        print(f"Task #{taskId} work {i} started")
        time.sleep(3)
        print(f"Task #{taskId} work {i} completed")
        if event.is_set():
            # End Task
            await ws.send("Task stopped")
            break
        await ws.send("Task completed")


def Worker(ws, taskId, event):
    asyncio.run(Task(ws, taskId, event))


async def NotifyListeners(message):
    for client in clients:
        await client.send(message)


def getTaskId(path):
    return str(path).replace("/", "").lower()


def StopTask(taskId):
    if taskId not in TASK_QUE:
        task = TASK_QUE["taskId"]
        _event = task["event"]
        _event.set()
        TASK_QUE.pop(taskId)


def RemoveTask(taskId):
    if taskId not in TASK_QUE:
        task = TASK_QUE["taskId"]
        _event = task["event"]
        _thread = task["thread"]
        if _thread.is_alive():  # Stop the thread if it is still active
            _event.set()
        TASK_QUE.pop(taskId)


def StartTask(taskId):
    if taskId not in TASK_QUE:
        task = TASK_QUE["taskId"]
        _thread = task["thread"]
        if not _thread.is_alive():
            _thread.start()


def addTask(ws, taskId, start=True):
    event = threading.Event()
    _thread = threading.Thread(target=Worker, args=(ws, taskId, event))
    if start:
        _thread.start()
    TASK_QUE[taskId] = {"thread": _thread, "event": event}


async def HandleClient(message, ws, path):
    taskId = getTaskId(
        path
    )  # URL should have a Task or Session Id e.g ws://127.0.0.1:2625/77776565/
    await NotifyListeners(message)
    if taskId not in TASK_QUE:
        addTask(ws, taskId)
    # You can send Events to start and stop specific tasks with StartTask(taskId) and StopTask(taskId)  from client using JSON
    ## URL Path


async def WebSocketServer(websocket, path):
    try:
        await register(websocket, path)
        async for message in websocket:
            await HandleClient(message, websocket, path)
    finally:
        await unregister(websocket, path)


async def Main():
    # Start server
    async with serve(WebSocketServer, "0.0.0.0", 2625):
        print(f"WebSocketServer Server started at port {2625}")
        await asyncio.Future()  # run forever


asyncio.run(Main())
