"""
Database class containing wrappers for the asyncpg pool instance.
"""
import asyncpg

import important

class Database():
    def __init__(self):
        self.__pool = None

    async def init(self):
        if self.__pool:
            return
        self.__pool = await asyncpg.create_pool(database=important.DATABASE,
                                              port=important.PORT,
                                              host=important.HOST,
                                              user=important.DB_USER,
                                              password=important.PASSWORD)
                                            
    async def execute(self, *args, **kwargs):
        """Wrapper for connection execute call"""
        connection = await self.__pool.acquire()
        try:
            results = await connection.execute(*args, **kwargs)
        finally:
            await self.__pool.release(connection)

        return results


    async def fetchrow(self, *args, **kwargs):
        """Wrapper for connection fetchrow call"""
        connection = await self.__pool.acquire()
        try:
            results = await connection.fetchrow(*args, **kwargs)
        finally:
            await self.__pool.release(connection)

        return results

    async def fetch(self, *args, **kwargs):
        """Wrapper for connection fetch call"""
        connection = await self.__pool.acquire()
        try:
            results = await connection.fetch(*args, **kwargs)
        finally:
            await self.__pool.release(connection)

        return results

    # Return simplified context manager
    def connect(self):
        return ConnectTo(self.__pool)

class ConnectTo():
    def __init__(self, pool):
        self.__pool = pool

    async def __aenter__(self):
        self.__connection = await self.__pool.acquire()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__pool.release(self.__connection)

    async def execute(self, *args, **kwargs):
        return await self.__connection.execute(*args, **kwargs)

    async def fetch(self, *args, **kwargs):
        return await self.__connection.fetch(*args, **kwargs)
        
    async def fetchrow(self, *args, **kwargs):
        return await self.__connection.fetchrow(*args, **kwargs)
