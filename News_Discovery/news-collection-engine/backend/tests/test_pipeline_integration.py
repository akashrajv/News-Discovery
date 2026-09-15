import pytest
from app.schemas.collection import CollectionRequestInput
from app.services.collection_service import CollectionService

@pytest.mark.asyncio
async def test_full_collection_pipeline(db_session):
    service = CollectionService(db_session)
    request_in = CollectionRequestInput(
        entity="Tata Motors",
        keywords=["EV", "electric vehicle"],
        location="India",
        category="Automotive",
        time_window_minutes=60
    )

    response = await service.execute_collection(request_in)

    assert response.status in ["success", "partial_success"]
    assert response.articles_collected > 0
    assert response.duplicates_removed >= 0
    assert response.request_id.startswith("req_")
    assert len(response.articles) > 0
    assert response.routing_summary is not None
