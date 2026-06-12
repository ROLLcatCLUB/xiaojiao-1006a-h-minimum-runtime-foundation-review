from __future__ import annotations
import argparse, json, sys, zipfile
from pathlib import Path
STAGE='1006F_MODEL_CANDIDATE_TO_WORK_OBJECT_PATCH_SANDBOX'
FINAL='XIAOJIAO_MODEL_CANDIDATE_TO_WORK_OBJECT_PATCH_SANDBOX_PASS'
SLUG='xiaojiao_model_candidate_to_work_object_patch_sandbox_1006F'
SAMPLE='model_candidate_to_work_object_patch_fixture_1006F.json'
MARKER='ALL_1006F_MODEL_CANDIDATE_TO_WORK_OBJECT_PATCH_SANDBOX_CHECKS_OK'
BAD_PARTS=[".env","token","secret","key","node_modules","__pycache__",".db",".sqlite","dist","build","coverage",".DS_Store"]
def fail(m): raise SystemExit(f'VALIDATION_FAILED: {m}')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); a=ap.parse_args(); root=Path(a.root).resolve() if a.root else Path(__file__).resolve().parents[1]
    req=[f'docs/foundation/{SLUG}.md',f'docs/foundation/{SLUG}.json',f'samples/{SLUG}/{SAMPLE}',f'docs/audit/{SLUG}_result.json',f'docs/audit/{SLUG}_report.md',f'docs/audit_packages/{SLUG}_manifest.json',f'scripts/validate_{SLUG}.py']
    for r in req:
        if not (root/r).exists(): fail(f'missing required file: {r}')
    contract=load(root/f'docs/foundation/{SLUG}.json'); sample=load(root/f'samples/{SLUG}/{SAMPLE}'); result=load(root/f'docs/audit/{SLUG}_result.json'); manifest=load(root/f'docs/audit_packages/{SLUG}_manifest.json')
    if contract.get('stage_code')!=STAGE or sample.get('stage_code')!=STAGE or result.get('stage_code')!=STAGE: fail('stage identity mismatch')
    if contract.get('final_status_target')!=FINAL or result.get('final_status')!=FINAL or result.get('pass') is not True or result.get('marker')!=MARKER: fail('result mismatch')
    for mapping in [contract.get('hard_boundaries',{}), sample.get('boundary_flags',{}), result.get('boundary_flags',{})]:
        for k,v in mapping.items():
            if v is not False: fail(f'unsafe boundary {k}')
    if STAGE.startswith('1006A'):
        if len(sample.get('modules',[])) < 10: fail('modules too few')
        if 'Teacher Review Gate' not in sample.get('modules',[]): fail('teacher review gate missing')
    elif STAGE.startswith('1006B'):
        events=[e.get('event_type') for e in sample.get('event_log',[])]
        for e in ['open_workbench','view_today','detect_pending_draft','confirm_draft','defer_current','request_generate_handout','candidate_patch_created','teacher_review_pending']:
            if e not in events: fail(f'missing event {e}')
        if sample.get('invariant_checks',{}).get('event_append_only') is not True or sample.get('invariant_checks',{}).get('real_database_written') is not False: fail('invariant mismatch')
    elif STAGE.startswith('1006C'):
        packs={p.get('business_pack_id') for p in sample.get('business_pack_registry',[])}
        for p in ['teaching_plan_pack','lesson_design_pack','resource_library_pack']:
            if p not in packs: fail(f'missing pack {p}')
        for o in ['semester_plan','today_work_items','lesson_design','handout','rubric','resource_ref']:
            if o not in sample.get('work_object_registry',[]): fail(f'missing object {o}')
    elif STAGE.startswith('1006D'):
        cases=sample.get('cases',[])
        if len(cases) < 4: fail('cases too few')
        if not any(c.get('parsed_intent')=='view_today' and c.get('token_cost')==0 for c in cases): fail('view today case missing')
        if not any(c.get('confirmed_intent')=='generate_handout' for c in cases): fail('clarification generate_handout missing')
    elif STAGE.startswith('1006E'):
        ids={d.get('directive_id') for d in sample.get('render_directives',[])}
        for i in ['light_entry_directive','focus_surface_directive','guided_flow_directive']:
            if i not in ids: fail(f'missing directive {i}')
    elif STAGE.startswith('1006F'):
        actions={f.get('action') for f in sample.get('flows',[])}
        if actions!={'generate_handout','revise_lesson_section'}: fail('flows mismatch')
        for f in sample.get('flows',[]):
            if f.get('teacher_review_required') is not True or f.get('direct_formal_write') is not False or f.get('database_written') is not False: fail('patch boundary mismatch')
    elif STAGE.startswith('1006G'):
        if sample.get('real_teacher_review_required') is not True or sample.get('system_cannot_auto_accept') is not True: fail('review gate mismatch')
        for a in ['teacher_accept_patch','teacher_reject_patch','teacher_request_revision']:
            if a not in sample.get('available_teacher_actions',[]): fail(f'missing review action {a}')
    elif STAGE.startswith('1006H'):
        final=sample.get('final_state',{})
        if final.get('teacher_review_required') is not True or final.get('formal_apply_performed') is not False: fail('final stop mismatch')
        if 'system stops before formal apply' not in sample.get('timeline',[]): fail('stop event missing')
    z=root/f'docs/audit_packages/{SLUG}.zip'
    if not z.exists(): fail('missing zip')
    with zipfile.ZipFile(z) as zf: entries=zf.namelist()
    for e in entries:
        n=e.replace('\\','/')
        if n.startswith('/') or ':' in n or '\\' in e: fail(f'unsafe zip path {e}')
        if any(part.lower() in n.lower() for part in BAD_PARTS): fail(f'forbidden zip entry {e}')
    if manifest.get('manifest_minus_zip')!=[] or manifest.get('zip_minus_manifest')!=[] or sorted(manifest.get('zip_entries',[]))!=sorted(entries): fail('manifest zip mismatch')
    print(MARKER); return 0
if __name__=='__main__': sys.exit(main())