import database

from accred import Accred


def has_privilege(user_id, privilege: Accred) -> int:
    accred = database.get_accred(user_id)
    if accred == -1:
        return -1
    else:
        return Accred.from_value(database.get_accred(user_id)) >= privilege
