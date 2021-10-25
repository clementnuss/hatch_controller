import threading

class AtomicBool:
    def __init__(self, initial: bool):
        self.value = initial
        self._lock = threading.Lock()
    
    def get(self):
        with self._lock:
            return self.value

    def set(self, new: bool):
        with self._lock:
            self.value = new
