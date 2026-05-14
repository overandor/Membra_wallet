from sqlalchemy.orm import Session

from app.models import AuditEvent


def audit(
    db: Session,
    event_type: str,
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    detail: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
