import discord

class NoNo_Word():
    def __init__(self, word: str):
        self.word = word # The nono_word iself
        self.count = 0
        self.jump_urls = [] # an array of url strings to all ocurrances of the nono_word
    
    def update_count(self, message_string):
        self.count += message_string.count(self.word)

    def add_jump_url(self, url: str):
        self.jump_urls.append(url)
