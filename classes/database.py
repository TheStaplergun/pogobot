"""
Database class containing wrappers for the asyncpg pool instance.
"""
import asyncpg

import important

class Database():
    def __init__(self):
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

    async def batch(self, coro_list) -> list:
        """Custom batch query wrapper for multiple database pool connection coroutines"""
        connection = await self.pool.acquire()
        results_list = []
        for coro in coro_list:
            try:
                results_list.append(await coro())
            finally:
                await self.pool.release(connection)

        return results_list
