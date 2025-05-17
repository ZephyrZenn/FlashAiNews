import threading


class AtomicValue:
    def __init__(self, initial=None):
        self._value = initial
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            return self._value

    def set(self, val):
        with self._lock:
            self._value = val

    def compare_and_set(self, expected, new_val):
        with self._lock:
            if self._value == expected:
                self._value = new_val
                return True
            return False

    def update(self, func):
        with self._lock:
            self._value = func(self._value)
            return self._value
