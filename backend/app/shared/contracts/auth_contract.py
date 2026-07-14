# Re-exported so other modules depend on auth's request dependency through the
# contract layer instead of importing app.modules.auth internals directly.
from app.modules.auth.dependencies import CurrentUser, get_current_user

__all__ = [
    "CurrentUser",
    "get_current_user",
]
