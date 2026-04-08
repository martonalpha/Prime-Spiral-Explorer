# Spatial Separation of Primes and Semiprimes
## In the Three-Dimensional Ulam Spiral

### An analysis of a visual observation

2025  
Preliminary draft, not peer-reviewed

## Abstract

This note documents and analyzes a visual observation arising from the arrangement of natural numbers in a three-dimensional Ulam spiral. When prime numbers (green points) and semiprimes, that is, products of two primes (red points), are plotted together in the 3D Ulam tower, a clear spatial separation appears: primes tend to concentrate in lower `z` regions, while semiprimes dominate higher regions and form a characteristic cone-like or pyramid-like boundary surface between the two sets. This separation is not accidental. It follows directly from the prime number theorem and from the asymptotic density of semiprimes. The observation suggests that 3D visualization can make structural differences visible that are harder to see, or only partially visible, in the classical 2D Ulam spiral.

## 1. Introduction

The Ulam spiral was discovered by Stanislaw Ulam in 1963 while he was sketching numbers during a conference lecture. The construction places natural numbers on a planar square spiral and marks the primes. The resulting image shows striking diagonal, horizontal, and vertical concentrations of prime numbers. This is remarkable because primes otherwise appear to be distributed in an irregular way.

The present project extends that idea into three dimensions. Numbers are positioned according to their Ulam spiral coordinates in the `xy` plane, but are also displaced along the `z` axis according to their rank within a selected sequence. In this project, the focus is on primes and semiprimes. The result is a tower-like 3D structure in which the familiar 2D patterns become vertically separated and new relationships become visible.

The most noticeable observation is that when primes and semiprimes are displayed simultaneously, the two point clouds separate clearly in 3D space. As argued below, this separation is deeply rooted in standard results from analytic number theory.

## 2. Basic concepts and notation

### 2.1 Prime numbers

A natural number `p` is prime if `p > 1` and its only positive divisors are `1` and `p`. The sequence begins:

`2, 3, 5, 7, 11, 13, 17, 19, 23, ...`

Let `pi(n)` denote the prime-counting function. By the prime number theorem,

`pi(n) ~ n / ln(n)` as `n -> infinity`.

This implies that the probability that a number near `n` is prime is approximately `1 / ln(n)`, so prime density decreases logarithmically.

### 2.2 Semiprimes

A natural number `n` is semiprime if it can be written as the product of exactly two primes, where the two primes may be equal:

`n = p * q`, where `p <= q` and both are prime.

Examples include:

`4 = 2*2, 6 = 2*3, 9 = 3*3, 10 = 2*5, 14 = 2*7, 15 = 3*5, ...`

Let `pi_2(n)` denote the number of semiprimes less than or equal to `n`. Its asymptotic growth is

`pi_2(n) ~ n * ln(ln(n)) / ln(n)`.

The factor `ln(ln(n))` grows extremely slowly, but it is enough to ensure that semiprimes eventually outnumber primes.

### 2.3 Construction of the 3D Ulam tower

The visualization is built as follows:

1. Natural numbers are placed in the `xy` plane according to the square Ulam spiral, with `1` at the center.
2. Primes and semiprimes are highlighted as separate sets.
3. Each highlighted number receives a `z` coordinate equal to its rank within its own set.
4. Primes are shown as green points, semiprimes as red points, and both sets are rendered together.

## 3. Description of the observation

The 3D Ulam tower visualization, based on numbers up to `27,449` in the initial screenshots and extended further in the project, exhibits the following visible phenomena.

### 3.1 Vertical separation

The green prime points concentrate primarily in lower `z` ranges and fill the lower body of the tower. The red semiprime points extend to substantially higher `z` values and dominate the upper and broader regions.

This follows directly from the different growth rates of the two counting functions. Primes become rarer among larger integers, while semiprimes remain comparatively denser. As a result, up to a given `n`, the semiprime rank grows faster than the prime rank.

### 3.2 A cone-like boundary surface

Between the two point clouds, one sees a characteristic surface that is approximately cone-like or pyramid-like. Geometrically, this is the region where primes and semiprimes occur in comparable proportions.

The boundary is not sharp. It behaves more like a gradient: primes dominate below, semiprimes dominate above. This is consistent with the fact that the ratio of `pi(n)` and `pi_2(n)` changes continuously and only approaches its asymptotic behavior gradually.

### 3.3 Lateral spread

Viewed from above, semiprimes cover a much larger area in the `xy` plane than primes. That is natural: semiprimes remain denser in the outer regions of the Ulam spiral, while primes tend to concentrate more strongly along the familiar diagonal patterns.

## 4. Mathematical background

### 4.1 Ratio of the densities

The reason for the separation lies in the ratio

`R(n) = pi_2(n) / pi(n) ~ ln(ln(n))`.

This ratio tells us how many semiprimes there are per prime up to `n`. Since `ln(ln(n)) -> infinity`, though very slowly, semiprimes eventually exceed primes by an arbitrarily large factor.

| `n` | `pi(n)` primes | `pi_2(n)` semiprimes | `R(n)` ratio |
| --- | ---: | ---: | ---: |
| 100 | 25 | 34 | 1.36 |
| 1,000 | 168 | 299 | 1.78 |
| 10,000 | 1,229 | 2,625 | 2.14 |
| 100,000 | 9,592 | 23,378 | 2.44 |
| 1,000,000 | 78,498 | 210,035 | 2.68 |

Table 1. Ratio of prime and semiprime counts for several values of `n`.

This gradual increase directly explains the vertical separation visible in the 3D tower.

### 4.2 Geometry of the boundary surface

Let `z_p(n)` be the rank of `n` among primes, and `z_sp(n)` the rank of `n` among semiprimes. Then

`z_p(n) = pi(n) ~ n / ln(n)`

and

`z_sp(n) = pi_2(n) ~ n * ln(ln(n)) / ln(n)`.

In both sets, the `z` coordinate is a monotone increasing function of the number itself, but the growth rates differ. Since the Ulam `xy` coordinates also depend on `n`, the geometry of the 3D point cloud reflects these density differences. The observed boundary surface is therefore not mysterious; it is a geometric rendering of different asymptotic counting laws.

### 4.3 Mod 6 structure and Ulam diagonals

In the classical Ulam spiral, primes tend to align along diagonal lines. This is connected to quadratic polynomials of the form `ax^2 + bx + c`, some of which generate unusually many primes over finite ranges.

Semiprimes behave more diffusely. In the `xy` plane they do not follow the diagonals as sharply, but instead tend to fill space between them more densely. In 3D this produces a broader and less line-like cloud than the prime cloud.

There is also a modular explanation. Every prime greater than `3` is congruent to `1` or `5` modulo `6`. Semiprimes have a wider residue behavior. This contributes to the different visual texture of the two sets.

## 5. Comparison and context

### 5.1 Comparing the two number classes

| Property | Primes | Semiprimes |
| --- | --- | --- |
| Definition | Divisible only by `1` and itself | Product of two primes |
| Asymptotic density | `pi(n) ~ n / ln(n)` | `pi_2(n) ~ n * ln(ln(n)) / ln(n)` |
| Dominance | Stronger for small `n` | Exceeds primes beyond a small threshold |
| 3D Ulam position | Concentrated lower | Extends higher and wider |
| Diagonal structure | Sharper, rarer lines | More diffuse and denser layers |
| Growth behavior | Slows by logarithmic law | Also slows, but remains relatively denser |

Table 2. High-level comparison between primes and semiprimes in this visualization context.

### 5.2 Relation to known results

The observed separation does not contradict known mathematics. On the contrary, it follows from it. The OEIS documents several semiprime-related sequences, including `A001358`, and classical literature already explains why primes exhibit visible structure in the Ulam spiral.

What is novel here is not a new theorem, but the visual extension into three dimensions. The 3D Ulam tower acts like a height map for arithmetic density: the `z` coordinate gives a direct visual signal of how quickly one counting function grows relative to another.

### 5.3 Relation to broader number theory

The study of prime distribution is closely connected to deeper themes such as the Riemann Hypothesis. This project does not provide evidence for such conjectures, but it does approach the same broad question from a different direction: where and how do primes appear when number sequences are embedded geometrically?

Semiprimes are also relevant in their own right, both in analytic number theory and in computational contexts. Their comparison with primes is therefore a useful test case for visualization-driven mathematical intuition.

## 6. Open questions and suggested investigations

The observation suggests several follow-up directions.

### 6.1 Precise description of the boundary surface

Can one describe explicitly the surface separating prime-dominated and semiprime-dominated regions in the 3D Ulam tower? One expects it to be linked to the equation `pi(n) = pi_2(n)`, but the Ulam coordinate transform makes the geometry nontrivial.

### 6.2 Higher-order prime products

What happens if one includes numbers with three or more prime factors? A natural conjecture is that one obtains layered shells or expanding strata above the semiprime region.

### 6.3 Alternative coordinate mappings

Does a similar separation appear in helix embeddings, Fibonacci sphere layouts, or other 3D coordinate systems? If yes, the phenomenon is likely not tied to one particular mapping, but to inherent arithmetic differences between the two classes.

### 6.4 Machine learning

Could the boundary between prime-like and semiprime-like regions be approximated by a learned model? Such a result would not replace primality testing, but it could be interesting as an exploratory classification problem.

### 6.5 Statistical significance

The visual separation is clear, but formal tests are still useful. One possible direction is a Kolmogorov-Smirnov comparison of the `z` coordinate distributions for the two sets.

## 7. Conclusions

When primes and semiprimes are plotted together in the three-dimensional Ulam spiral, a clear and mathematically grounded spatial separation appears. This separation:

- follows directly from the prime number theorem and the asymptotic semiprime density formula,
- forms a characteristic cone-like boundary in 3D space,
- is much harder to see in the standard 2D Ulam spiral,
- and motivates several further mathematical and computational investigations.

The value of the visualization is therefore not that it replaces theory, but that it makes theory visible. The prime-versus-semiprime separation is a geometrically intuitive rendering of known arithmetic facts, and may serve as a useful starting point for deeper exploration.

## References

1. Ulam, S. M. (1964). *An observation on the distribution of primes*. American Mathematical Monthly, 74, 43-44.
2. Gardner, M. (1964). *Mathematical Games*. Scientific American, 210(3).
3. Hardy, G. H., and Littlewood, J. E. (1923). *Some problems of Partitio Numerorum*. Acta Mathematica, 44, 1-70.
4. OEIS Foundation (2024). *A001358: Semiprimes*. The On-Line Encyclopedia of Integer Sequences. https://oeis.org/A001358
5. Apostol, T. M. (1976). *Introduction to Analytic Number Theory*. Springer.
6. Landau, E. (1909). *Handbuch der Lehre von der Verteilung der Primzahlen*. Teubner, Leipzig.
7. 3Blue1Brown (2019). *Why do prime numbers make these spirals?* https://www.3blue1brown.com/lessons/prime-spirals
