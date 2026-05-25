from app.shared.events.decorators import subscribe_to
from app.shared.events.event_bus import DomainEvent

@subscribe_to("UserRegistered")
async def on_user_registered(event: DomainEvent) -> None: pass

@subscribe_to("UserLoggedIn")
async def on_user_logged_in(event: DomainEvent) -> None: pass

@subscribe_to("UserPasswordReset")
async def on_user_password_reset(event: DomainEvent) -> None: pass

@subscribe_to("UserRoleChanged")
async def on_user_role_changed(event: DomainEvent) -> None: pass
