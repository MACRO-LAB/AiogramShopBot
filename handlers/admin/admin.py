import inspect
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from callbacks import AdminMenuCallback, AdminAnnouncementCallback, AdminInventoryManagementCallback, \
    UserManagementCallback, StatisticsCallback
from handlers.admin.announcement import announcement_router
from handlers.admin.inventory_management import inventory_management
from handlers.admin.statistics import statistics
from handlers.admin.user_management import user_management
from utils.custom_filters import AdminIdFilter
from utils.localizator import Localizator, BotEntity

admin_router = Router()
admin_router.include_router(announcement_router)
admin_router.include_router(inventory_management)
admin_router.include_router(user_management)
admin_router.include_router(statistics)


@admin_router.message(F.text == Localizator.get_text(BotEntity.ADMIN, "menu"), AdminIdFilter())
async def admin_command_handler(message: types.message):
    await admin(message)


async def admin(message: Message | CallbackQuery):
    admin_menu_builder = InlineKeyboardBuilder()
    admin_menu_builder.button(text=Localizator.get_text(BotEntity.ADMIN, "announcements"),
                              callback_data=AdminAnnouncementCallback.create(level=0))
    admin_menu_builder.button(text=Localizator.get_text(BotEntity.ADMIN, "inventory_management"),
                              callback_data=AdminInventoryManagementCallback.create(level=0))
    admin_menu_builder.button(text=Localizator.get_text(BotEntity.ADMIN, "user_management"),
                              callback_data=UserManagementCallback.create(level=0))
    admin_menu_builder.button(text=Localizator.get_text(BotEntity.ADMIN, "statistics"),
                              callback_data=StatisticsCallback.create(level=0))
    admin_menu_builder.button(text=Localizator.get_text(BotEntity.ADMIN, "crypto_withdraw"),
                              callback_data=AdminMenuCallback.create(level=22))
    admin_menu_builder.adjust(2)
    if isinstance(message, Message):
        await message.answer(Localizator.get_text(BotEntity.ADMIN, "menu"),
                             reply_markup=admin_menu_builder.as_markup())
    elif isinstance(message, CallbackQuery):
        callback = message
        await callback.message.edit_text(Localizator.get_text(BotEntity.ADMIN, "menu"),
                                         reply_markup=admin_menu_builder.as_markup())


# async def wallet(callback: CallbackQuery):
#     cb_builder = InlineKeyboardBuilder()
#     cb_builder.row(
#         types.InlineKeyboardButton(text=Localizator.get_text(BotEntity.ADMIN, "withdraw_funds"),
#                                    callback_data=create_admin_callback(level=23)))
#     cb_builder.row(AdminConstants.back_to_main_button)
#     await callback.message.edit_text(Localizator.get_text(BotEntity.ADMIN, "crypto_withdraw"),
#                                      reply_markup=cb_builder.as_markup())


# async def send_withdraw_crypto_menu(callback: CallbackQuery):
#     cb_builder = InlineKeyboardBuilder()
#     cb_builder.row(AdminConstants.back_to_main_button)
#     await callback.message.edit_text(Localizator.get_text(BotEntity.ADMIN, 'choose_crypto_to_withdraw'),
#                                      reply_markup=cb_builder.as_markup())


@admin_router.callback_query(AdminIdFilter(), AdminMenuCallback.filter())
async def admin_menu_navigation(callback: CallbackQuery, state: FSMContext, callback_data: AdminMenuCallback):
    current_level = callback_data.level

    levels = {
        0: admin,
        # 22: wallet,
        # 23: send_withdraw_crypto_menu
    }

    current_level_function = levels[current_level]
    if inspect.getfullargspec(current_level_function).annotations.get("state") == FSMContext:
        await current_level_function(callback, state)
    else:
        await current_level_function(callback)
