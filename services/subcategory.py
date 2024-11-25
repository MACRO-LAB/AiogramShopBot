import math

from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func, delete
import config
from callbacks import AllCategoriesCallback
from db import session_commit, session_execute, session_refresh, get_db_session
from handlers.common.common import add_pagination_buttons
from handlers.user.constants import UserConstants
from models.item import Item, ItemDTO
from models.subcategory import Subcategory
from repositories.category import CategoryRepository
from repositories.item import ItemRepository
from repositories.subcategory import SubcategoryRepository
from utils.localizator import Localizator, BotEntity


class SubcategoryService:

    @staticmethod
    async def get_or_create_one(subcategory_name: str) -> Subcategory:
        async with get_db_session() as session:
            stmt = select(Subcategory).where(Subcategory.name == subcategory_name)
            subcategory = await session_execute(stmt, session)
            subcategory = subcategory.scalar()
            if subcategory is None:
                new_category_obj = Subcategory(name=subcategory_name)
                session.add(new_category_obj)
                await session_commit(session)
                await session_refresh(session, new_category_obj)
                return new_category_obj
            else:
                return subcategory

    @staticmethod
    async def get_to_delete(page: int = 0) -> list[Subcategory]:
        async with get_db_session() as session:
            stmt = select(Subcategory).join(Item,
                                            Item.subcategory_id == Subcategory.id).where(
                Item.is_sold == 0).distinct().limit(config.PAGE_ENTRIES).offset(
                page * config.PAGE_ENTRIES).group_by(Subcategory.name)
            subcategories = await session_execute(stmt, session=session)
            subcategories = subcategories.scalars().all()
            return subcategories

    @staticmethod
    async def get_maximum_page():
        async with get_db_session() as session:
            stmt = select(func.count(Subcategory.id)).distinct()
            subcategories = await session_execute(stmt, session)
            subcategories_count = subcategories.scalar_one()
            if subcategories_count % SubcategoryService.items_per_page == 0:
                return subcategories_count / SubcategoryService.items_per_page - 1
            else:
                return math.trunc(subcategories_count / SubcategoryService.items_per_page)

    @staticmethod
    async def get_maximum_page_to_delete():
        async with get_db_session() as session:
            unique_categories_subquery = (
                select(Subcategory.id)
                .join(Item, Item.subcategory_id == Subcategory.id)
                .filter(Item.is_sold == 0)
                .distinct()
            ).alias('unique_categories')
            stmt = select(func.count()).select_from(unique_categories_subquery)
            max_page = await session_execute(stmt, session)
            max_page = max_page.scalar_one()
            if max_page % config.PAGE_ENTRIES == 0:
                return max_page / config.PAGE_ENTRIES - 1
            else:
                return math.trunc(max_page / config.PAGE_ENTRIES)

    @staticmethod
    async def get_by_primary_key(subcategory_id: int) -> Subcategory:
        async with get_db_session() as session:
            stmt = select(Subcategory).where(Subcategory.id == subcategory_id)
            subcategory = await session_execute(stmt, session)
            return subcategory.scalar()

    @staticmethod
    async def delete_if_not_used(subcategory_id: int):
        # TODO("Need testing")
        async with get_db_session() as session:
            stmt = select(Subcategory).join(Item, Item.subcategory_id == subcategory_id).where(
                Subcategory.id == subcategory_id)
            result = await session_execute(stmt, session)
            if result.scalar() is None:
                stmt = delete(Subcategory).where(Subcategory.id == subcategory_id)
                await session_execute(stmt, session)
                await session_commit(session)

    # new methods________________
    @staticmethod
    async def get_buttons(callback: CallbackQuery) -> InlineKeyboardBuilder:
        unpacked_cb = AllCategoriesCallback.unpack(callback.data)
        kb_builder = InlineKeyboardBuilder()
        subcategories = await SubcategoryRepository.get_paginated_by_category_id(unpacked_cb.category_id,
                                                                                 unpacked_cb.page)
        for subcategory in subcategories:
            item = await ItemRepository.get_single(unpacked_cb.category_id, subcategory.id)
            available_qty = await ItemRepository.get_available_qty(ItemDTO(category_id=unpacked_cb.category_id,
                                                                           subcategory_id=subcategory.id))
            kb_builder.button(text=Localizator.get_text(BotEntity.USER, "subcategory_button").format(
                subcategory_name=subcategory.name,
                subcategory_price=item.price,
                available_quantity=available_qty,
                currency_sym=Localizator.get_currency_symbol()),
                callback_data=AllCategoriesCallback.create(
                    unpacked_cb.level + 1,
                    unpacked_cb.category_id,
                    subcategory.id
                )
            )
        kb_builder.adjust(1)
        kb_builder = await add_pagination_buttons(kb_builder, unpacked_cb,
                                                  SubcategoryRepository.max_page(unpacked_cb.category_id),
                                                  UserConstants.get_back_button(unpacked_cb))
        return kb_builder

    @staticmethod
    async def get_select_quantity_buttons(callback: CallbackQuery) -> tuple[str, InlineKeyboardBuilder]:
        unpacked_cb = AllCategoriesCallback.unpack(callback.data)
        item = await ItemRepository.get_single(unpacked_cb.category_id, unpacked_cb.subcategory_id)
        subcategory = await SubcategoryRepository.get_by_id(unpacked_cb.subcategory_id)
        category = await CategoryRepository.get_by_id(unpacked_cb.category_id)
        available_qty = await ItemRepository.get_available_qty(item)
        message_text = Localizator.get_text(BotEntity.USER, "select_quantity").format(
            category_name=category.name,
            subcategory_name=subcategory.name,
            price=item.price,
            description=item.description,
            quantity=available_qty,
            currency_sym=Localizator.get_currency_symbol()
        )
        kb_builder = InlineKeyboardBuilder()
        for i in range(1, 11):
            kb_builder.button(text=str(i), callback_data=AllCategoriesCallback.create(
                unpacked_cb.level + 1,
                item.category_id,
                item.subcategory_id,
                quantity=i
            ))
        kb_builder.adjust(3)
        kb_builder.row(UserConstants.get_back_button(unpacked_cb))
        return message_text, kb_builder

    @staticmethod
    async def get_add_to_cart_buttons(callback: CallbackQuery) -> tuple[str, InlineKeyboardBuilder]:
        unpacked_cb = AllCategoriesCallback.unpack(callback.data)
        item = await ItemRepository.get_single(unpacked_cb.category_id, unpacked_cb.subcategory_id)
        category = await CategoryRepository.get_by_id(unpacked_cb.category_id)
        subcategory = await SubcategoryRepository.get_by_id(unpacked_cb.subcategory_id)
        message_text = Localizator.get_text(BotEntity.USER, "buy_confirmation").format(
            category_name=category.name,
            subcategory_name=subcategory.name,
            price=item.price,
            description=item.description,
            quantity=unpacked_cb.quantity,
            total_price=item.price * unpacked_cb.quantity,
            currency_sym=Localizator.get_currency_symbol())
        kb_builder = InlineKeyboardBuilder()
        kb_builder.button(text=Localizator.get_text(BotEntity.COMMON, "confirm"),
                          callback_data=AllCategoriesCallback.create(
                              unpacked_cb.level + 1,
                              unpacked_cb.category_id,
                              unpacked_cb.subcategory_id,
                              quantity=unpacked_cb.quantity,
                              confirmation=True
                          ))
        kb_builder.button(text=Localizator.get_text(BotEntity.COMMON, "cancel"),
                          callback_data=AllCategoriesCallback.create(
                              1,
                              unpacked_cb.category_id
                          ))
        kb_builder.row(UserConstants.get_back_button(unpacked_cb))
        return message_text, kb_builder
