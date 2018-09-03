from enum import Enum


class EventTypes(Enum):
    """
    An Enum that contains the different event types that are possible
    """
    SCRAPING_EXECUTION_FINISHED = 0


class ScrapingExecutionFinishedEventData:
    """
    Payload data for the SCRAPING_EXECUTION_FINISHED event
    """
    def __init__(self, exec_status, billing_info):
        self.billing_info = billing_info
        self.exec_status = exec_status


class Observer:
    """
    All classes interested in observing an event must inherit from this class
    and set to observe a certain event. All subclasses must call Observer.__init__(self)
    in their constructor. When an Event is instantiated and fired, all observers listening
    to that event will run the specified callback functions.
    """
    _observers = []

    def __init__(self):
        self._observers.append(self)
        self._observables = {}

    def observe(self, event_type, callback):
        """
        Set yourself up as an observer for a particular event
        :param event_type: EventType object
        :param callback: the callback that is called when the event_type event is fired
        """
        self._observables[event_type] = callback


class Event:
    """
    The Event in the Observer/Event framework (see documentation on Observer class)
    """
    def __init__(self, event_type, data, autofire=True):
        """
        :param event_type: EventType object
        :param data: the data payload that is packaged with the event
        :param autofire: whether or not to fire the event on instantiation
        """
        self.type = event_type
        self.data = data
        if autofire:
            self.fire()

    def fire(self):
        """
        Fire the event and notify all listeners
        """
        for observer in Observer._observers:
            if self.type in observer._observables:
                observer._observables[self.type](self.data)
