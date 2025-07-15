# task4.py
numbers_list = [1, 3, 2, 4, 3, 1, 2, 5, 10]

# Count occurrences of each number
occurrences = {}
for num in numbers_list:
    if num in occurrences:
        occurrences[num] += 1
    else:
        occurrences[num] = 1

# Print numbers that appear more than once
print("Numbers that appear more than once:")
for num, count in occurrences.items():
    if count > 1:
        print(num)
