import invoke

@invoke.task
def buildlambda(c):
    c.run("python -m pip install -U -t dist/lambda .")
    with c.cd("dist/lambda"):
        c.run("zip -x '*.pyc' -r ../lambda.zip .")
