from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from database.unit_of_work import UnitOfWork
from keyboards.buttons import AdminCallbackFactory, get_main_menu_keyboard
from keyboards.filters import (
    FiltersCallbackFactory,
    get_back_to_filter_menu,
    get_filters_list_for_group,
    get_groups_list_for_filters,
)
from loguru import logger


router = Router()


class FilterStates(StatesGroup):
    """Состояния для FSM при работе с фильтрами"""

    waiting_for_int_value = State()  # Ожидание ввода целочисленного значения


@router.callback_query(AdminCallbackFactory.filter(F.action == "filters_menu"))
async def group_filters_menu(query: CallbackQuery, uow: UnitOfWork):
    groups = await uow.group_service.get_all_groups()
    await query.message.edit_text(
        _("select_group"), reply_markup=get_groups_list_for_filters(groups)
    )


@router.callback_query(FiltersCallbackFactory.filter(F.action == "filters"))
async def filters_menu(
    callback: CallbackQuery, uow: UnitOfWork, callback_data: FiltersCallbackFactory
):
    group_id = callback_data.group_id

    # Получаем фильтры для группы
    filters = await uow.filter_service.get_group_filters(group_id)

    if not filters:
        await callback.message.answer(
            text=_("no-filters-found"),
            reply_markup=get_groups_list_for_filters(
                await uow.group_service.get_all_groups()
            ),
        )
        return

    # Получаем информацию о группе для заголовка
    group = await uow.group_service.get_group_by_id(group_id)
    group_name = group.title if group else _("unknown-group")

    await callback.message.edit_text(
        text=_("filters-for-group").format(group_name=group_name),
        reply_markup=get_filters_list_for_group(filters),
    )


@router.callback_query(FiltersCallbackFactory.filter(F.action == "update"))
async def filter_update_menu(
    callback: CallbackQuery,
    uow: UnitOfWork,
    callback_data: FiltersCallbackFactory,
    state: FSMContext,
):
    group_id = callback_data.group_id
    filter_key = callback_data.key
    current_value = callback_data.value
    if isinstance(current_value, bool):
        new_value = bool(not current_value)

        # Обновляем фильтр
        await uow.filter_service.update_filter_by_name(group_id, filter_key, new_value)

        # Получаем обновленные фильтры
        filters = await uow.filter_service.get_group_filters(group_id)
        group = await uow.group_service.get_group_by_id(group_id)
        group_name = group.title if group else _("unknown-group")

        await callback.message.edit_text(
            text=_("filter-updated-success").format(group_name=group_name),
            reply_markup=get_filters_list_for_group(filters),
        )
    else:
        # Определяем тип фильтра для подсказки пользователю
        filter_names = {
            "max_message_length": _("filter-max-message-length"),
            "bonus_per_user": _("filter-bonus-per-user"),
            "bonus_checkpoint": _("filter-bonus-checkpoint"),
        }
        filter_display_name = filter_names.get(filter_key, filter_key)
        # Сохраняем данные в состоянии FSM
        await state.update_data(
            group_id=group_id, filter_key=filter_key, current_value=current_value
        )
        # Устанавливаем состояние ожидания ввода значения
        await state.set_state(FilterStates.waiting_for_int_value)

        # Отправляем сообщение с инструкцией
        await callback.message.edit_text(
            text=_("enter-value").format(
                filter_name=filter_display_name, current_value=current_value
            ),
            reply_markup=get_back_to_filter_menu(group_id),
        )


@router.message(FilterStates.waiting_for_int_value)
async def process_custom_value(message: Message, state: FSMContext, uow: UnitOfWork):
    # Получаем данные из состояния
    data = await state.get_data()
    group_id = data.get("group_id")
    filter_key = data.get("filter_key")
    current_value = data.get("current_value")

    # Проверяем введенное значение
    try:
        new_value = int(message.text.strip())

        # Проверяем диапазон значений в зависимости от типа фильтра
        valid_value = True
        error_message = ""

        if filter_key == "max_message_length":
            if new_value < 10 or new_value > 4000:
                valid_value = False
                error_message = _("invalid-message-length-range")
        elif filter_key == "bonus_per_user":
            if new_value < 1 or new_value > 100:
                valid_value = False
                error_message = _("invalid-bonus-per-user-range")
        elif filter_key == "bonus_checkpoint":  # noqa: SIM102
            if new_value < 100 or new_value > 10000:
                valid_value = False
                error_message = _("invalid-bonus-checkpoint-range")

        if not valid_value:
            await message.answer(
                text=error_message,
                reply_markup=get_back_to_filter_menu(
                    group_id, filter_key, current_value
                ),
            )
            await state.clear()
            return

        # Обновляем фильтр
        await uow.filter_service.update_filter_by_name(group_id, filter_key, new_value)

        # Получаем обновленные фильтры и информацию о группе
        filters = await uow.filter_service.get_group_filters(group_id)
        group = await uow.group_service.get_group_by_id(group_id)
        group_name = group.title if group else _("unknown-group")

        # Отправляем сообщение об успешном обновлении
        await message.answer(
            text=_("filter-updated-success").format(group_name=group_name),
            reply_markup=get_filters_list_for_group(filters),
        )

    except ValueError:
        # Если введено не число
        await message.answer(
            text=_("invalid-number-format"),
            reply_markup=get_back_to_filter_menu(group_id, filter_key, current_value),
        )
    except Exception as e:
        # Если произошла другая ошибка
        logger.error(f"Ошибка при обновлении фильтра: {e}")
        await message.answer(
            text=_("filter-update-error"),
            reply_markup=get_main_menu_keyboard(user_role="admin"),
        )

    # Очищаем состояние
    await state.clear()
