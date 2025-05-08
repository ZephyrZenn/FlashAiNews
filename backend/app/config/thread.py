from concurrent.futures import ThreadPoolExecutor

thread_pool = None

def init_thread_pool():
    global thread_pool
    thread_pool = ThreadPoolExecutor(max_workers=4)

def get_thread_pool():
    global thread_pool
    if thread_pool is None:
        init_thread_pool()
    return thread_pool

def shutdown_thread_pool():
    global thread_pool
    if thread_pool is not None:
        thread_pool.shutdown(wait=True)
        thread_pool = None


