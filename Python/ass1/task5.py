# task5.py
students_scores = [('John', 85), ('Maria', 92), ('Tom', 76), ('Sarah', 90)]

# Find the student with the highest score
highest_score = students_scores[0]
for student, score in students_scores:
    if score > highest_score[1]:
        highest_score = (student, score)

print("Student with the highest score:", highest_score[0], "with a score of", highest_score[1])
