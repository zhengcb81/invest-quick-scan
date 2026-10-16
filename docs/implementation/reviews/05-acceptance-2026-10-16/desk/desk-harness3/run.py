import datetime, hashlib, json, os, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parent
LAB=ROOT.parent/'desk3'
def main():
    tag=sys.argv[1]
    tmp=ROOT/'tmp'; tmp.mkdir(exist_ok=True)
    env={k:os.environ[k] for k in ('SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA') if k in os.environ}
    env.update(PYTHONPATH=str(ROOT)+os.pathsep+str(LAB),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',TEMP=str(tmp),TMP=str(tmp),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    argv=[sys.executable,'-B','-X','utf8','-m','pytest','-p','no:cacheprovider','-q',*sys.argv[2:]]
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    p=subprocess.run(argv,cwd=LAB,env=env,capture_output=True)
    end=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for name,data in [('stdout',p.stdout),('stderr',p.stderr)]: (ROOT/f'{tag}.{name}.txt').write_bytes(data)
    record=dict(argv=argv,cwd=str(LAB),started=start,ended=end,exit_code=p.returncode,environment='minimal-no-key; audit deny external writes and external Python socket network; TEMP explicit review root',stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest())
    (ROOT/f'{tag}.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record)); print(p.stdout.decode('utf-8',errors='replace')[-8000:]); print(p.stderr.decode('utf-8',errors='replace')[-2000:])
    return p.returncode
if __name__=='__main__':sys.exit(main())
