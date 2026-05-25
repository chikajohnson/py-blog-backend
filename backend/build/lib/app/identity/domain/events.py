from app.shared.events.event_bus import DomainEvent


def user_registered(user_id: str, email: str, role: str) -> DomainEvent:
    return DomainEvent(event_type="UserRegistered", payload={"user_id": user_id, "email": email, "role": role}, source="identity")

def user_logged_in(user_id: str, ip_address: str) -> DomainEvent:
    return DomainEvent(event_type="UserLoggedIn", payload={"user_id": user_id, "ip_address": ip_address}, source="identity")

def user_password_reset(user_id: str) -> DomainEvent:
    return DomainEvent(event_type="UserPasswordReset", payload={"user_id": user_id}, source="identity")

def user_role_changed(user_id: str, old_role: str, new_role: str, changed_by: str) -> DomainEvent:
    return DomainEvent(event_type="UserRoleChanged", payload={"user_id": user_id, "old_role": old_role, "new_role": new_role, "changed_by": changed_by}, source="identity")
