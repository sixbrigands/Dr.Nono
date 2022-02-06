from table2ascii import table2ascii as t2a, PresetStyle

left_aligned = "Left Align"
center = "Centered"
right_aligned = "Right Align"

# nono_string = "Hello!\n"

# nono_string += "{left_aligned:.<15}{right_aligned:>10}".format(
#     left_aligned=left_aligned,
#     right_aligned=right_aligned)



# In your command:
output = t2a(
    header=["Rank", "Team", "Kills", "Position Pts", "Total"],
    body=[[1, 'Team A', 2, 4, 6], [2, 'Team B', 3, 3, 6], [3, 'Team C', 4, 2, 6]],
    first_col_heading=True
)
print(output)