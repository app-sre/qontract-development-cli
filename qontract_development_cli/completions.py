from .models import Env, Profile


def complete_env() -> list[str]:
    return [e.name for e in Env.list_all()]


def complete_profile() -> list[str]:
    return [p.name for p in Profile.list_all()]
