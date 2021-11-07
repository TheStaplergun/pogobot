class Lobby():
    """
    A class containing various pieces of cached data about a lobbym
    """
    def __init__(self, bot, user_limit, user_count, lobby_id, raid_id, host):
        self.__bot = bot
        self.user_limit = user_limit
        self.user_count = user_count
        self.lobby_id = lobby_id
        self.raid_id = raid_id
        self.host = host

    def add_a_user(self):
        self.user_count+=1
        return self.user_count

    def remove_a_user(self):
        self.user_count-=1

    def is_full(self):
        return self.user_count == self.user_limit
