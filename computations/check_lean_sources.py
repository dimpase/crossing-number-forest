#!/usr/bin/env python3
"""Static source inventory and correspondence checks, not Lean elaboration."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
LEAN=ROOT/'source-material/openai-math/lean'
PREFIX='OAI.Combinatorics.Crossing.'

def uncomment(s):
    # Lean block comments nest. Preserve line breaks for useful locations.
    out=[]; i=0; depth=0
    while i<len(s):
        if s[i:i+2]=='/-': depth+=1; out.append('  '); i+=2
        elif depth and s[i:i+2]=='-/': depth-=1; out.append('  '); i+=2
        elif depth: out.append('\n' if s[i]=='\n' else ' '); i+=1
        elif s[i:i+2]=='--':
            j=s.find('\n',i)
            if j<0:j=len(s)
            out.append(' '*(j-i));i=j
        else: out.append(s[i]);i+=1
    assert depth==0
    return ''.join(out)

def declaration(s,name):
    match=re.search(r'^(?:def|abbrev|structure) '+re.escape(name)+r'\b',s,re.M)
    assert match, name
    rest=s[match.start():]
    following=re.search(r'\n(?:def|abbrev|structure|theorem|lemma) ',rest)
    assert following, name
    return ' '.join(rest[:following.start()].split())

def run():
    paths=sorted((LEAN/'OAI/Combinatorics/Crossing').glob('*.lean'))
    graph={};decls={};forbidden=[];mathlib=set()
    for p in paths:
        s=uncomment(p.read_text())
        module='.'.join(p.relative_to(LEAN).with_suffix('').parts)
        imports=re.findall(r'^import\s+(\S+)',s,re.M)
        graph[module]=[x for x in imports if x.startswith('OAI.')]
        mathlib.update(x for x in imports if x.startswith('Mathlib.'))
        assert all(x.startswith(('OAI.','Mathlib.','Lean.')) for x in imports),(module,imports)
        for m in re.finditer(r'\b(sorry|admit|axiom|unsafe|native_decide|implemented_by|extern)\b',s):
            forbidden.append([module,s[:m.start()].count('\n')+1,m.group()])
        decls[module]=re.findall(r'^(?:theorem|lemma|def|abbrev|structure)\s+(\S+)',s,re.M)
    assert not forbidden, forbidden
    seen=set()
    def walk(m,chain):
        assert m in graph, ('Missing project import',m)
        assert m not in chain, ('Import cycle',m)
        if m in seen:return
        for target in graph[m]:walk(target,chain+[m])
        seen.add(m)
    walk(PREFIX+'Main',[])
    assert len(seen)==339 and seen==set(graph)
    challenge=uncomment((LEAN/'ComparatorChallenges/BipartiteCrossing.lean').read_text())
    drawing=uncomment((LEAN/'OAI/Combinatorics/Crossing/DrawingDefinition.lean').read_text())
    shared=['Plane','BipartiteVertex','BipartiteEdge','ContinuousDrawing','edgeInterior',
            'ProperCrossing','crossingPoints','AdmissibleDrawing','crossingCount','MainTarget']
    for name in shared:
        assert declaration(challenge,name)==declaration(drawing,name),name
    cfg=json.loads((LEAN/'ComparatorChallenges/BipartiteCrossing.json').read_text())
    assert cfg['solution_module']==PREFIX+'Main'
    assert cfg['theorem_names']==['OAI.Zarankiewicz.mainTarget_proof']
    assert cfg['permitted_axioms']==['propext','Quot.sound','Classical.choice']
    assert cfg['enable_nanoda'] is False
    assert re.findall(r'\b(?:sorry|admit)\b',challenge)==['sorry']
    # Check each curated paper-to-Lean correspondence against a real declaration.
    map_path=ROOT/'lean-map.json'
    if map_path.exists():
        for row in json.loads(map_path.read_text())['correspondences']:
            assert row['declaration'] in decls[PREFIX+row['module']],row
            assert (ROOT/'trees'/f"{row['note']}.tree").exists(),row
    record={'scope':'Static source inspection only; Lean and Comparator were not run locally.',
            'project_modules':len(seen),'project_bytes':sum(p.stat().st_size for p in paths),
            'external_libraries':['Mathlib','Lean'],'direct_mathlib_imports':len(mathlib),
            'forbidden_source_tokens':forbidden,'challenge_definition_matches':shared,
            'permitted_axioms':cfg['permitted_axioms'],'enable_nanoda':cfg['enable_nanoda'],
            'imports':graph,'declarations':decls}
    dest=ROOT/'computations/lean-source-audit.json'
    if '--write' in sys.argv:dest.write_text(json.dumps(record,indent=2)+'\n')
    else:assert json.loads(dest.read_text())==record,'Source audit differs from stored record'
    print(f'PASS: all {len(seen)} Crossing modules belong to Main\'s complete project-import closure; imports outside that closure are Mathlib and Lean.')
    print('PASS: no sorry/admit/axiom/unsafe/native_decide/implemented_by/extern tokens in uncommented proof sources.')
    print('PASS: ten shared challenge/solution declarations match textually; the challenge has its expected single sorry placeholder.')
    print('These are source checks, not a Lean build, kernel axiom audit, or Comparator run.')

if __name__=='__main__':run()
