You task is to write Python program solutions to the given math problems.


## Example
**Question**
Solve for $a$: $\\dfrac{8^{-1}}{4^{-1}}-a^{-1}=1$.

**Solution**
```python
a = symbols('a')
eq = (8**(-1))/(4**(-1)) - a**(-1) - 1
solution = solve(eq, a)
a_value = solution[0]
print(a_value)
```
**Tools**
```python
from sympy import symbols, solve
```


## Example
**Question**
${question}

**Solution**
