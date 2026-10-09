#!/usr/bin/env python3
"""Exact finite examples for the detector; not a proof of the general theorem."""
from itertools import permutations
from pathlib import Path
import json, sys
import sympy as S

ROOT = Path(__file__).resolve().parent

def example(s):
    n = 2*s+1
    nodes = list(map(S.Integer, range(1, n+1)))
    weights = [1/S.prod(x-y for y in nodes if y != x) for x in nodes]
    vectors = {(p,q): S.Matrix([nodes[p]**a*nodes[q]**b for a in range(s) for b in range(s)])
               for p in range(n) for q in range(n)}
    atoms = {(p,q): (nodes[p]-nodes[q])*weights[p]*weights[q]*h*h.T
             for (p,q),h in vectors.items()}
    zero = S.zeros(s*s)
    for p in range(n):
        assert sum((atoms[p,q] for q in range(n)), zero) == zero
        assert sum((atoms[q,p] for q in range(n)), zero) == zero
        for q in range(n):
            assert atoms[p,q].rank() == int(p != q)
    pattern = [(p,q) for p in range(n) for q in range(n)
               if (q < p <= s) or (s < p < q)]
    A = S.Matrix.hstack(*(vectors[p,q] for p,q in pattern))
    assert len(pattern) == s*s and A.det() != 0
    orders = list(permutations(range(n))) if n <= 5 else [tuple(range(n)), tuple(reversed(range(n))), tuple(range(1,n))+ (0,), (2,5,0,6,1,4,3)]
    natural = None
    for order in orders:
        pos = {p:i for i,p in enumerate(order)}
        image = sum((S.Rational(1 if pos[p]<pos[q] else -1, 2)*atoms[p,q]
                     for p in range(n) for q in range(n) if p!=q), zero)
        assert image.det() != 0
        Q = [(order[p],order[q]) for p,q in pattern]
        AQ = S.Matrix.hstack(*(vectors[p,q] for p,q in Q))
        DQ = S.diag(*[(1 if pos[p] <= s else -1)*(nodes[p]-nodes[q])*weights[p]*weights[q] for p,q in Q])
        assert image == -AQ*DQ*AQ.T
        if order == tuple(range(n)): natural = image
    return {'s':s,'n':n,'dimension':s*s,'nodes':list(range(1,n+1)),
            'weights':list(map(str,weights)), 'pattern':[[p+1,q+1] for p,q in pattern],
            'evaluation_determinant':str(A.det()),'orders_checked':len(orders),
            'natural_order_image':[[str(x) for x in row] for row in natural.tolist()],
            'natural_order_determinant':str(natural.det())}

def run():
    results=[example(s) for s in (1,2,3)]
    for m in range(1,31):
        d=(m//2)*((m-1)//2)
        assert m*m-m-2*(m*m//4)==2*d
        if m>2 and m%2==0:
            prev=((m-1)//2)*((m-2)//2)
            assert m*prev==(m-2)*d
        a,b=m//2,(m+1)//2
        assert a*b==m*m//4
    record={'scope':'Exact finite checks for n=3,5,7; not general proof or a Lean build.',
            'examples':results,'integer_identities_checked_through':30}
    path=ROOT/'examples.json'
    if '--write' in sys.argv:
        path.write_text(json.dumps(record,indent=2)+'\n')
    else:
        assert json.loads(path.read_text())==record, 'Stored exact examples differ'
    print('PASS: exact atom ranks, row/column cancellation, two-triangle bases, and order factorizations.')
    print('Checked all 6 orders for n=3, all 120 for n=5, and 4 specified orders for n=7.')
    print('PASS: floor/deletion identities and sharpness arithmetic through 30.')
    print('These finite examples do not verify the general crossing-number theorem.')

if __name__ == '__main__': run()
