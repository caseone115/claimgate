import subprocess, sys, os
ROOT = "/home/john-douglas"
AB = ROOT + "/.npm/_npx/ad6c181e5b604bdb/node_modules/agent-browser/bin/agent-browser.js"
PROFILE = ROOT + "/claimgate/state/gumroad-profile"
SANDBOX = "--no-sandbox,--disable-dev-shm-usage"
def ab(*args, stdin=None, timeout=300, profile=True, sandbox=True):
    cmd = ["node", AB]
    if profile:
        cmd += ["--profile", PROFILE]
    cmd += ["--session", "gumroad"]
    if sandbox:
        cmd += ["--args", SANDBOX]
    cmd += [str(a) for a in args]
    p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    return (p.stdout or "") + (p.stderr or "")
if __name__ == "__main__":
    print(ab(*sys.argv[1:]))
