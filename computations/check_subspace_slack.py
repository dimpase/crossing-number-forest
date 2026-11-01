#!/usr/bin/env python3
"""Exact finite illustrations of the subspace-deficit identity.

Uses actual constrained polynomial spaces over Q. This is not a proof of
the general lemma, a Lean run, or a kernel/axiom audit. No repository code
is imported or executed. Requires SymPy.
"""

import json
import random
import sys
from pathlib import Path

import sympy as sp


def require(condition, message):
    if not condition:
        raise ValueError(message)


def basis(n, indices):
    indices = list(indices)
    return sp.eye(n)[:, indices] if indices else sp.zeros(n, 0)


def joined(n, matrices):
    return sp.Matrix.hstack(*matrices) if matrices else sp.zeros(n, 0)


def intersection_dimension(a, b):
    return a.cols + b.cols - a.row_join(b).rank()


def annihilator(a):
    vectors = a.T.nullspace()
    return sp.Matrix.hstack(*vectors).T if vectors else sp.zeros(0, a.rows)


def polynomial_data(u, nodes, z, degree, at):
    """Return dim P_degree(Z), and its evaluated column space at 'at'."""
    n, dimension = z.shape
    unknowns = dimension * (degree + 1)
    rows = []
    for subspace, node in zip(u, nodes):
        az = annihilator(subspace) * z
        rows.append(sp.Matrix.hstack(*(node ** power * az for power in range(degree + 1))))
    constraint = sp.Matrix.vstack(*rows) if rows else sp.zeros(0, unknowns)
    require(constraint.cols == unknowns, "constraint matrix shape")
    kernel = constraint.nullspace()
    coefficients = sp.Matrix.hstack(*kernel) if kernel else sp.zeros(unknowns, 0)
    evaluation = sp.Matrix.hstack(*(at ** power * z for power in range(degree + 1)))
    return unknowns - constraint.rank(), evaluation * coefficients


def run_case(name, u, v, nodes=None, expected_deficit=None):
    m = len(u)
    require(m >= 1 and len(v) == m, name + ": family sizes")
    n = u[0].rows
    nodes = list(range(1, m + 1)) if nodes is None else nodes
    require(len(nodes) == m and len(set(nodes)) == m, name + ": nodes")
    tstar = min(nodes) - 1
    require(tstar not in nodes, name + ": non-node")
    for i in range(m):
        require(u[i].rows == n and v[i].rows == n, name + ": ambient dimension")
        require(u[i].rank() == u[i].cols and v[i].rank() == v[i].cols, name + ": bases")
        require(intersection_dimension(u[i], v[i]) == 0, name + ": disjointness")

    all_k = []
    w_evaluations = []
    for z_index, z in enumerate([sp.eye(n)] + v):
        previous = 0
        increments = []
        for h in range(m):
            dimension, values = polynomial_data(u, nodes, z, h, tstar)
            increment = dimension - previous
            require(increment >= 0, name + ": nonnegative k")
            require(values.rank() == increment, name + ": off-node evaluation identity")
            increments.append(increment)
            previous = dimension
            if z_index == 0:
                w_evaluations.append(values)
        all_k.append(increments)

    kw = all_k[0]
    kv = all_k[1:]
    ell = [kw[h] - (kw[h - 1] if h else 0) for h in range(m)]
    require(all(e >= 0 for e in ell), name + ": nonnegative filtration increments")
    r = sum(ell)
    require(r == joined(n, u).rank(), name + ": r equals dim sum U_i")
    require(r == w_evaluations[-1].rank(), name + ": r equals final evaluation rank")

    # Independently inspect the ranks at constraint nodes, not just non-nodes.
    for h in range(m):
        for j, node in enumerate(nodes):
            _, values = polynomial_data(u, nodes, sp.eye(n), h, node)
            require(values.rank() <= kw[h] - kv[j][h], name + ": node-rank loss")

    intersections = [[intersection_dimension(a, b) for b in v] for a in u]
    total = sum(sum(row) for row in intersections)
    for j in range(m):
        require(sum(kv[j]) == sum(intersections[i][j] for i in range(m)),
                name + ": all-node interpolation identity")

    c = m * m // 4
    stage_slacks = [sum(e * ell[e] for e in range(h + 1)) - sum(k[h] for k in kv)
                    for h in range(m)]
    require(all(d >= 0 for d in stage_slacks), name + ": degree budgets")
    weights = [c - e * (m - e) for e in range(m)]
    require(all(w >= 0 for w in weights), name + ": nonnegative weights")
    deficit = c * n - total
    ambient_slack = c * (n - r)
    noncentral_slack = sum(weights[e] * ell[e] for e in range(m))
    require(ambient_slack >= 0, name + ": ambient slack")
    require(deficit == ambient_slack + noncentral_slack + sum(stage_slacks),
            name + ": exact deficit identity")

    if m >= 2:
        central = {m // 2, (m + 1) // 2}
        equality_conditions = (r == n and all(ell[e] == 0 for e in range(m) if e not in central)
                               and all(d == 0 for d in stage_slacks))
        require((deficit == 0) == equality_conditions, name + ": equality criterion")
        k = m // 2
        refined_weights = [(e - k) ** 2 if m % 2 == 0 else (e - k) * (e - k - 1)
                           for e in range(m)]
        require(weights == refined_weights, name + ": parity weight formulas")
        outside = sum(ell[e] for e in range(m) if e not in central)
        require(outside <= (deficit if m % 2 == 0 else deficit // 2),
                name + ": noncentral-column stability")
        require(n - r <= deficit // c, name + ": ambient stability")
        require(sum(stage_slacks) <= deficit, name + ": stage stability")
    else:
        require(c == 0 and deficit == 0 and stage_slacks == [0], name + ": m=1 boundary")

    if expected_deficit is not None:
        require(deficit == expected_deficit, name + ": expected deficit")
    return dict(name=name, m=m, N=n, nodes=nodes, total_intersection_dimension=int(total),
                deficit=int(deficit), r=int(r), ell=list(map(int, ell)),
                stage_slacks=list(map(int, stage_slacks)))


def random_invertible(n, rng):
    matrix = sp.eye(n)
    if n >= 2:
        for _ in range(3 * n + 1):
            a, b = rng.sample(range(n), 2)
            factor = rng.choice([-2, -1, 1, 2])
            matrix[a, :] = matrix[a, :] + factor * matrix[b, :]
    require(matrix.det() != 0, "random change of basis invertible")
    return matrix


def main():
    cases = []
    # Coordinate equality construction, including zero space and m=1.
    for m in [1, 2, 3, 4, 5, 6]:
        for n in [0, 1, 3]:
            p = basis(n, range(n // 2))
            q = basis(n, range(n // 2, n))
            split = m // 2
            u = [p if i < split else q for i in range(m)]
            v = [q if i < split else p for i in range(m)]
            cases.append(run_case(f"sharp_m{m}_n{n}", u, v, expected_deficit=0))

    # Deliberately noncentral columns with the smallest positive weight.
    for m, expected in [(4, 1), (5, 2)]:
        u = [sp.eye(1)] + [sp.zeros(1, 0) for _ in range(m - 1)]
        v = [sp.zeros(1, 0)] + [sp.eye(1) for _ in range(m - 1)]
        cases.append(run_case(f"near_equality_m{m}", u, v, expected_deficit=expected))

    cases.append(run_case("m1_unused_ambient", [sp.zeros(2, 0)], [sp.eye(2)], expected_deficit=0))
    require(cases[-1]["r"] < cases[-1]["N"], "m=1 must not imply r=N")

    # Exact non-coordinate examples. Different changes of basis for each pair
    # avoid assuming all spaces share a common coordinate basis.
    rng = random.Random(20261101)
    for number, (n, m) in enumerate([(2, 2), (2, 3), (2, 4), (3, 3),
                                    (3, 4), (3, 5), (4, 3), (4, 4)]):
        u, v = [], []
        for _ in range(m):
            change = random_invertible(n, rng)
            a = rng.randint(1, n - 1)
            b = rng.randint(1, n - a)
            u.append(change[:, :a])
            v.append(change[:, a:a + b])
        cases.append(run_case(f"noncoordinate_{number}_m{m}_n{n}", u, v))

    # The filtration may depend on the interpolation-node tuple.
    u = [sp.Matrix([1, i]) for i in range(1, 5)]
    v = [sp.zeros(2, 0) for _ in range(4)]
    regular = run_case("node_dependence_regular", u, v, [1, 2, 3, 4])
    perturbed = run_case("node_dependence_perturbed", u, v, [1, 2, 3, 5])
    require(regular["ell"] != perturbed["ell"], "filtration profile changes with nodes")
    require(regular["r"] == perturbed["r"] and regular["deficit"] == perturbed["deficit"],
            "total deficit and span do not change with nodes")
    cases.extend([regular, perturbed])

    result = dict(status="passed", scope="Exact finite illustration only; not a universal proof or Lean verification.",
                  arithmetic="SymPy exact rational linear algebra", seed=20261101,
                  case_count=len(cases), cases=cases)
    path = Path(__file__).with_name("subspace-slack.json")
    if "--write" in sys.argv:
        path.write_text(json.dumps(result, indent=2) + "\n")
    else:
        require(json.loads(path.read_text()) == result, "Stored subspace-slack examples differ")
    print("PASS: 31 exact rational subspace-slack cases and stored results match.")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}, indent=2))
    print("Detailed results:", path)


if __name__ == "__main__":
    main()
