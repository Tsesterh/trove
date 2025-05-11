import math

count = 0
for i in range(2, 100 + 1):
    for j in range(2, int(math.sqrt(i)) + 1):
        if i % j == 0:
            break
    else:
        count += 1
print(count)