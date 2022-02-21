#!/usr/bin/env python
import multiprocessing
import resource

max_cpu_cores = multiprocessing.cpu_count()
print(f"Max CPU cores for multiprocessing: {max_cpu_cores}")

max_open_files = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
print(f"Max Open Files/Sockets for asyncio IO: {max_open_files:,}")
