from aiogram.filters.callback_data import CallbackData

class BaseCallback(CallbackData, prefix="base"):
    level: int

    def back_button_cb(self):
        level = self.level - 1
        self.level = level
        return self.create(**self.model_dump())


class AllCategoriesCallback(BaseCallback, prefix="all_categories"):
    category_id: int
    subcategory_id: int
    price: float
    quantity: int
    total_price: float
    confirmation: bool
    page: int

    @staticmethod
    def create(level: int,
               category_id: int = -1,
               subcategory_id: int = -1,
               price: float = 0.0,
               total_price: float = 0.0,
               quantity: int = 0,
               confirmation: bool = False,
               page: int = 0):
        return AllCategoriesCallback(level=level, category_id=category_id, subcategory_id=subcategory_id, price=price,
                                     total_price=total_price,
                                     quantity=quantity, confirmation=confirmation, page=page)


class MyProfileCallback(BaseCallback, prefix="my_profile"):
    action: str
    args_for_action: int | str
    page: int

    @staticmethod
    def create(level: int, action: str = "", args_for_action="", page=0):
        return MyProfileCallback(level=level, action=action, args_for_action=args_for_action, page=page).pack()
