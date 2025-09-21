import asyncio

class EventBus():
    ''' Event bus'''
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name: str) -> None:
        ''' Subscribe for an event in the bus '''
        def upper(func):
            self.listeners[event_name] = self.listeners.get(event_name, set())
            self.listeners[event_name].add(func)
            return func
        return upper # type: ignore

    def unsubscribe(self, event_name: str, listener) -> None:
        ''' Unsubscribe for an event in the bus '''
        self.listeners[event_name].remove(listener)
        if len(self.listeners[event_name]) == 0:
            del self.listeners[event_name]

    def emit(self, event_name: str, *args, **kwargs) -> None:
        ''' Emit an event in the bus '''
        listeners = self.listeners.get(event_name, [])
        for listener in listeners:
            asyncio.create_task(listener(*args, **kwargs))

bus = EventBus()