---
title: Math Environments
md_flavor: math
---

# Envs
Aligned and cases with labels and refs.

$$
\begin{aligned}
a^2 + b^2 &= c^2 \\
c &= \sqrt{a^2+b^2}
\end{aligned}
$$

Numbered:
$$
\begin{equation}\label{eq:bayes}
P(A\mid B)=\frac{P(B\mid A)P(A)}{P(B)}
\end{equation}
$$
See Eq. \(\ref{eq:bayes}\).

Alt delimiter:
\[
\sum_{k=1}^{n} k = \frac{n(n+1)}{2}
\]

Code fence with escaped dollars:
```bash
echo "Total: \$99.00"
```
