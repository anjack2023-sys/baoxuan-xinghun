import json,re,statistics
from pathlib import Path
from verify_match_logs import read
root=Path('C:/BeybladeUE')
result={'baseline':85,'time_limit_seconds':60,'fixed_hz':60,'SPIN_KICK':1.3,'RESTITUTION':0.9,'seeds':[]}
for seed in (4242,42,2026):
 paths=[]
 for fps in (60,120):
  log=(root/f'Saved/Battle-auto-{seed}-{fps}.log').read_text(encoding='utf-8')
  assert 'BATTLE_AUTO_COMPLETE matches=24' in log
  match=re.search(r'BATTLE_READY[^\n]*log=([^\r\n]+)',log)
  assert match, 'missing CSV path'
  paths.append(root/'Saved/BattleLogs'/Path(match[1].strip()).name)
 a,b=map(read,paths)
 assert a==b and 'time_limit_s=60' in a[0]
 rows=a[1]
 old_report=json.loads((root/'Tools/feel85_verification.json').read_text(encoding='utf-8'))
 old_path=Path(next(item for item in old_report['seeds'] if item['seed']==seed)['logs'][0])
 old_rows=read(old_path)[1]
 assert [r['first_hit'] for r in rows]==[r['first_hit'] for r in old_rows], 'launch/first contact changed'
 result['seeds'].append({'seed':seed,'logs':list(map(str,paths)),'identical':True,'matches':len(rows),'ringout':sum(r['end_reason']=='ringout' for r in rows),'timeout':sum(r['end_reason']=='timeout' for r in rows),'mean_end_seconds':statistics.mean(float(r['end_t']) for r in rows),'mean_hits':statistics.mean(int(r['hit_count']) for r in rows)})
result['replay_result']='PASS'
(root/'Tools/feel85_60s_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
