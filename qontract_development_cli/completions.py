from .models import (
    Env,
    Profile,
)


def complete_env():
    return [e.name for e in Env.list_all()]


def complete_profile():
    return [p.name for p in Profile.list_all()]
