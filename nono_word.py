import discord

class NoNo_Word():
    def __init__(self, word: str, count: int = 0, jump_url: str = ''):
        self.word = word # The nono_word iself
        self.count = count
        self.jump_urls = [jump_url] # an array of url strings to all ocurrances of the nono_word
    
    # Update word count with a message broken into a list of strings
    def update_count(self, message_list: list):
        self.count += message_list.count(self.word)

    # Add reference url to list
    def add_jump_url(self, url: str):
        self.jump_urls.append(url)

    # Update all fields
    def update(self, message_list: list, url :str):
        self.update_count(message_list)
        self.add_jump_url(url)
