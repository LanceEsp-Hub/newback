# task3.py
people = {'profile': {'John': 19, 'Emily': 21, 'Sarah': 25, 'Tom': 18}}

# Print names of people older than 19
print("People older than 19:")
for name, age in people['profile'].items():
    if age > 19:
        print(name)
