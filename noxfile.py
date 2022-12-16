import nox


def all_sessions(session):
    session.install("-U", "pip")
    session.install(".[tests]")
    session.run("pytest")


@nox.session(python="python3.8")
def python38(session):
    return all_sessions(session)


@nox.session(python="python3.9")
def python39(session):
    return all_sessions(session)


@nox.session(python="python3.10")
def python310(session):
    return all_sessions(session)
