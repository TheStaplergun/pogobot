"""
Database class containing wrappers for the asyncpg pool instance.
"""
import asyncpg

import important

class Database():
    """
    This database class is a wrapper for an asynchronous connection pool to a postgres database.
    It can be directly used as a context manager through the connect method for batch queries,
    or individual queries can be made with the other methods.
    """
    def __init__(self, pool):
        self.__pool = pool

    # Return simplified context manager
    def connect(self):
        """
        Allows multiple queries to be executed within a single connection under a
        context manager.
        """
        return self.__pool.acquire()

    async def execute(self, *args, **kwargs):
        """Wrapper for single execute call"""
        async with self.__pool.acquire() as c:
            return await c.execute(*args, **kwargs)

    async def fetchrow(self, *args, **kwargs):
        """Wrapper for single fetchrow call"""
        async with self.__pool.acquire() as c:
            return await c.fetchrow(*args, **kwargs)

    async def fetch(self, *args, **kwargs):
        """Wrapper for single fetch call"""
        async with self.__pool.acquire() as c:
            return await c.fetch(*args, **kwargs)

    # class __ConnectTo():
    #     def __init__(self, pool):
    #         self.__pool = pool

    #     async def __aenter__(self):
    #         self.__connection = await self.__pool.acquire()
    #         return self
    #     async def __aexit__(self, exc_type, exc_val, exc_tb):
    #         await self.__pool.release(self.__connection)

    #     async def execute(self, *args, **kwargs):
    #         return await self.__connection.execute(*args, **kwargs)

    #     async def fetch(self, *args, **kwargs):
    #         return await self.__connection.fetch(*args, **kwargs)
            
    #     async def fetchrow(self, *args, **kwargs):
    #         return await self.__connection.fetchrow(*args, **kwargs)
