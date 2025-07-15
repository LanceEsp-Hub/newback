# task2.py
numbers = (1, 4, 7, 10, 13, 16)

# Sum and count odd numbers
odd_sum = 0
odd_count = 0
for num in numbers:
    if num % 2 != 0:
        odd_sum += num
        odd_count += 1

# Calculate and print average of odd numbers
if odd_count > 0:
    average = odd_sum / odd_count
    print("Average of odd numbers:", average)
