from sqlalchemy import select, func, update

from db import get_db_session, session_execute, session_commit
from models.buyItem import BuyItem, BuyItemDTO
from models.item import Item, ItemDTO


class ItemRepository:

    @staticmethod
    async def get_price(item_dto: ItemDTO) -> float:
        stmt = (select(Item.price)
                .where(Item.category_id == item_dto.category_id,
                       Item.subcategory_id == item_dto.subcategory_id)
                .limit(1))
        async with get_db_session() as session:
            price = await session_execute(stmt, session)
            return price.scalar()

    @staticmethod
    async def get_available_qty(item_dto: ItemDTO) -> int:
        sub_stmt = (select(Item)
                    .where(Item.category_id == item_dto.category_id,
                           Item.subcategory_id == item_dto.subcategory_id,
                           Item.is_sold == False))
        stmt = select(func.count()).select_from(sub_stmt)
        async with get_db_session() as session:
            available_qty = await session_execute(stmt, session)
            return available_qty.scalar()

    @staticmethod
    async def get_single(category_id: int, subcategory_id: int):
        stmt = (select(Item)
                .where(Item.category_id == category_id,
                       Item.subcategory_id == subcategory_id,
                       Item.is_sold == False)
                .limit(1))
        async with get_db_session() as session:
            item = await session_execute(stmt, session)
            return ItemDTO.model_validate(item.scalar(), from_attributes=True)

    @staticmethod
    async def get_by_id(item_id: int):
        stmt = select(Item).where(Item.id == item_id)
        async with get_db_session() as session:
            item = await session_execute(stmt, session)
            return ItemDTO.model_validate(item.scalar(), from_attributes=True)

    @staticmethod
    async def get_purchased_items(category_id: int, subcategory_id: int, quantity: int) -> list[ItemDTO]:
        stmt = (select(Item)
                .where(Item.category_id == category_id, Item.subcategory_id == subcategory_id,
                       Item.is_sold == False).limit(quantity))
        async with get_db_session() as session:
            items = await session_execute(stmt, session)
            return [ItemDTO.model_validate(item, from_attributes=True) for item in items.scalars().all()]

    @staticmethod
    async def update(item_dto_list: list[ItemDTO]):
        async with get_db_session() as session:
            for item in item_dto_list:
                stmt = update(Item).where(Item.id == item.id).values(**item.model_dump())
                await session_execute(stmt, session)
            await session_commit(session)

    @staticmethod
    async def get_by_buy_id(buy_id: int) -> list[ItemDTO]:
        stmt = (
            select(Item)
            .join(BuyItem, BuyItem.item_id == Item.id)
            .where(BuyItem.buy_id == buy_id)
        )
        async with get_db_session() as session:
            result = await session_execute(stmt, session)
            return [ItemDTO.model_validate(item, from_attributes=True) for item in result.scalars().all()]
