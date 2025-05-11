You task is to write Python program solutions to the given math problems.
You should also create Python functions that can be used by your solution, if you believe the function can be reused to solve other questions.


## Example
**Question**
A group of 10 Caltech students go to Lake Street for lunch. Each student eats at either Chipotle or Panda Express. In how many different ways can the students collectively go to lunch?
**Solution**
```python
ways = 2**10
print(ways)
```
**Tools**
```python
import math
```

## Example
**Question**
Four-digit integers are formed using the digits 2, 3, 4 and 5. Any of the digits can be used any number of times. How many such four-digit integers are palindromes? Palindromes read the same forward and backward.
**Solution**
```python
count = 0
for digit1 in [2, 3, 4, 5]:
    for digit2 in [2, 3, 4, 5]:
        for digit3 in [2, 3, 4, 5]:
            for digit4 in [2, 3, 4, 5]:
                number = digit1 * 1000 + digit2 * 100 + digit3 * 10 + digit4
                if str(number) == str(number)[::-1]:
                    count += 1
print(count)
```
**Tools**
```python
import math
```


## Example
**Question**
${question}

**Solution**
