import us


JURISDICTION_NAMES = [
    s.name
    for s in us.STATES
    + [us.states.PR, us.states.DC]
]
JURISDICTIONS = [
    s
    for s in us.STATES
    + [us.states.PR, us.states.DC]
]


def find_jurisdiction(jur_name: str):
    """
    Return a github.com/unitedstates/python-us style
    jurisdiction object so we can (potentially) back fill
    """
    for jurisdiction in JURISDICTIONS:
        if jur_name == jurisdiction.name:
            return jurisdiction
