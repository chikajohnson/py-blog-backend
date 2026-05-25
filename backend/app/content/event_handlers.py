from app.shared.events.decorators import subscribe_to
from app.shared.events.event_bus import DomainEvent

@subscribe_to("ArticlePublished")
async def on_article_published(event: DomainEvent) -> None: pass

@subscribe_to("ArticleViewed")
async def on_article_viewed(event: DomainEvent) -> None: pass

@subscribe_to("ArticleCreated")
async def on_article_created(event: DomainEvent) -> None: pass

@subscribe_to("ArticleDeleted")
async def on_article_deleted(event: DomainEvent) -> None: pass

@subscribe_to("CategoryCreated")
async def on_category_created(event: DomainEvent) -> None: pass

@subscribe_to("TagCreated")
async def on_tag_created(event: DomainEvent) -> None: pass
