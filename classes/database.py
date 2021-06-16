"""
Database class containing wrappers for the asyncpg pool instance.
"""
import asyncpg

import important

class Database():
    def __init__(self):
        self.pool = None

    async def init(self):
        if self.pool:
            return
        self.pool = await asyncpg.create_pool(database=important.DATABASE,
                                              port=important.PORT,
                                              host=important.HOST,
                                              user=important.DB_USER,
                                              password=important.PASSWORD)
                                            
    async def execute(self, *args, **kwargs):
        """Wrapper for connection execute call"""
        connection = await self.pool.acquire()
        try:
            results = await connection.execute(*args, **kwargs)
        finally:
            await self.pool.release(connection)

        return results


    async def fetchrow(self, *args, **kwargs):
        """Wrapper for connection fetchrow call"""
        connection = await self.pool.acquire()
        try:
            results = await connection.fetchrow(*args, **kwargs)
        finally:
            await self.pool.release(connection)

        return results

    async def fetch(self, *args, **kwargs):
        """Wrapper for connection fetch call"""
        connection = await self.pool.acquire()
        try:
            results = await connection.fetch(*args, **kwargs)
        finally:
            await self.pool.release(connection)

        return results

    # Set up context manager
    async def connect(self):
        context = ConnectTo(self.pool)
        return context

class ConnectTo():
    def __init__(self, pool):
        self.pool = pool
    async def __aenter__(self):
        self.connection = self.pool.acquire()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.pool.release(connection)

    # async def batch(self, coro_list) -> list:
    #     """Custom batch query wrapper for multiple database pool connection coroutines"""

    #     async with BatchQuery(self.pool) as bq:

    #         pass
    #     return results_list



# class DBConnection(object):
#     """database connection"""
#     def __init__(self, connection_string):
#         self.connection_string = connection_string
#         self.session = None
#     def __enter__(self):
#         engine = create_engine(self.connection_string)
#         Session = sessionmaker()
#         self.session = Session(bind=engine)
#         return self
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.session.close()
