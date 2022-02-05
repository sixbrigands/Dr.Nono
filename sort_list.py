with open('bad_words.txt', 'r') as f:
    with open('bad_words_shortened.txt', 'w') as f2:
        nono_list = f.readlines()
        for bad_word in nono_list:
            if input(bad_word) != 'n':
                f2.write(bad_word)

# with open('bad_words_shortened.txt', 'r') as f:
#     with open('bad_words_shortened2.txt', 'w') as f2:
#         nono_list = f.readlines()
#         for bad_word in nono_list:
#             if len(bad_word) > 2:
#                 f2.write(bad_word)