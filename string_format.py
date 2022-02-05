left_aligned = "Left Align"
center = "Centered"
right_aligned = "Right Align"

nono_string = "Hello!\n"

nono_string += "{left_aligned:.<15}{right_aligned:>10}".format(
    left_aligned=left_aligned,
    right_aligned=right_aligned)

print(nono_string)