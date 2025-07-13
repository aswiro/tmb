from datetime import datetime, timedelta
from decimal import Decimal

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from database.services.ad_analytics_service import AdAnalyticsService
from database.services.ad_campaign_service import AdCampaignService
from database.services.ad_creative_service import AdCreativeService
from database.services.advertiser_service import AdvertiserService
from filters.admins import AdminFilter
from filters.advertisers import AdvertiserFilter
from keyboards.ads import (
    get_admin_ad_menu,
    get_advertiser_details_keyboard,
    get_advertiser_menu,
    get_all_advertisers_keyboard,
    get_all_campaigns_keyboard,
    get_campaign_confirmation_keyboard,
    get_campaign_created_keyboard,
    get_campaign_details_keyboard,
    get_create_campaign_cancel_keyboard,
    get_creative_moderation_keyboard,
    get_end_date_keyboard,
    get_moderation_queue_keyboard,
    get_my_campaigns_keyboard,
    get_no_campaigns_keyboard,
    get_rejection_reason_keyboard,
    get_start_date_keyboard,
)
from keyboards.buttons import AdCallbackFactory
from loguru import logger


router = Router()


# Хендлеры для обычных рекламодателей
@router.callback_query(
    AdCallbackFactory.filter(F.action == "ad_menu" & F.role == "advertiser"),
    AdvertiserFilter(),
)
async def advertiser_menu(call: CallbackQuery, session):
    """Меню рекламодателя"""
    await call.answer()

    advertiser_service = AdvertiserService(session)
    advertiser = await advertiser_service.get_advertiser(call.from_user.id)

    if not advertiser:
        await call.message.edit_text(_("advertiser-not-found"), reply_markup=None)
        return

    text = _(
        "advertiser-menu",
        company_name=advertiser.company_name,
        balance=advertiser.balance,
    )

    await call.message.edit_text(text, reply_markup=get_advertiser_menu())


@router.callback_query(
    AdCallbackFactory.filter(F.action == "my_campaigns"), AdvertiserFilter()
)
async def my_campaigns(call: CallbackQuery, session):
    """Мои рекламные кампании"""
    await call.answer()

    campaign_service = AdCampaignService(session)
    advertiser_service = AdvertiserService(session)

    advertiser = await advertiser_service.get_advertiser(call.from_user.id)
    if not advertiser:
        await call.message.edit_text(
            _("advertiser-not-found"), reply_markup=get_advertiser_menu()
        )
        return

    campaigns = await campaign_service.get_campaigns_by_advertiser(advertiser.id)

    if not campaigns:
        text = _("no-campaigns", company_name=advertiser.company_name)
        await call.message.edit_text(text, reply_markup=get_no_campaigns_keyboard())
        return

    # Формируем текст со списком кампаний
    text_lines = [_("my-campaigns-header", company_name=advertiser.company_name)]
    text_lines.append("")

    for i, campaign in enumerate(
        campaigns[:10], 1
    ):  # Ограничиваем до 10 кампаний на страницу
        # Определяем эмодзи статуса
        status_emoji = {
            "draft": "📝",
            "active": "✅",
            "paused": "⏸️",
            "completed": "✔️",
            "archived": "📦",
        }.get(campaign.status.value, "❓")

        # Вычисляем процент потраченного бюджета
        budget_percent = (
            (campaign.spent_amount / campaign.budget * 100)
            if campaign.budget > 0
            else 0
        )

        campaign_info = _(
            "campaign-info",
            number=i,
            name=campaign.name,
            status_emoji=status_emoji,
            status=_(f"status-{campaign.status.value}"),
            spent=campaign.spent_amount,
            budget=campaign.budget,
            percent=budget_percent,
        )
        text_lines.append(campaign_info)

    text = "\n".join(text_lines)

    await call.message.edit_text(
        text,
        reply_markup=get_my_campaigns_keyboard(campaigns),
        parse_mode="HTML",
    )


@router.callback_query(
    AdCallbackFactory.filter(F.action == "campaign_details"), AdvertiserFilter()
)
async def campaign_details(
    call: CallbackQuery, callback_data: AdCallbackFactory, session
):
    """Детали рекламной кампании"""
    await call.answer()

    campaign_service = AdCampaignService(session)
    advertiser_service = AdvertiserService(session)

    # Проверяем, что кампания принадлежит пользователю
    advertiser = await advertiser_service.get_advertiser(call.from_user.id)
    if not advertiser:
        return

    campaign = await campaign_service.get_campaign_by_id(callback_data.item_id)
    if not campaign or campaign.advertiser_id != advertiser.id:
        await call.message.edit_text(
            _("campaign-not-found"), reply_markup=get_my_campaigns_keyboard()
        )
        return

    # Получаем статистику кампании
    analytics_service = AdAnalyticsService(session)
    stats = await analytics_service.get_campaign_stats(campaign.id)

    # Формируем детальную информацию
    status_emoji = {
        "draft": "📝",
        "active": "✅",
        "paused": "⏸️",
        "completed": "✔️",
        "archived": "📦",
    }.get(campaign.status.value, "❓")

    text = _(
        "campaign-details",
        name=campaign.name,
        status_emoji=status_emoji,
        status=_(f"status-{campaign.status.value}"),
        budget=campaign.budget,
        spent=campaign.spent_amount,
        remaining=campaign.budget - campaign.spent_amount,
        start_date=campaign.start_date.strftime("%d.%m.%Y %H:%M"),
        end_date=campaign.end_date.strftime("%d.%m.%Y %H:%M"),
        impressions=stats.get("impressions", 0),
        clicks=stats.get("clicks", 0),
        ctr=stats.get("ctr", 0.0),
    )

    await call.message.edit_text(
        text,
        reply_markup=get_campaign_details_keyboard(campaign),
        parse_mode="HTML",
    )


class CreateCampaignStates(StatesGroup):
    """Состояния для создания кампании"""

    waiting_for_name = State()
    waiting_for_budget = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()
    confirmation = State()


@router.callback_query(
    AdCallbackFactory.filter(F.action == "create_campaign"), AdvertiserFilter()
)
async def create_campaign_start(call: CallbackQuery, state: FSMContext, session):
    """Начало создания новой кампании"""
    await call.answer()

    # Проверяем, что пользователь является рекламодателем
    advertiser_service = AdvertiserService(session)
    advertiser = await advertiser_service.get_advertiser(call.from_user.id)

    if not advertiser:
        await call.message.edit_text(
            _("advertiser-not-found"), reply_markup=get_advertiser_menu()
        )
        return

    # Сохраняем ID рекламодателя в состоянии
    await state.update_data(advertiser_id=advertiser.id)

    # Переходим к вводу названия кампании
    await state.set_state(CreateCampaignStates.waiting_for_name)

    text = _("create-campaign-enter-name", company_name=advertiser.company_name)

    await call.message.edit_text(
        text, reply_markup=get_create_campaign_cancel_keyboard()
    )


@router.message(CreateCampaignStates.waiting_for_name, AdvertiserFilter())
async def create_campaign_name(message: Message, state: FSMContext):
    """Обработка названия кампании"""
    campaign_name = message.text.strip()

    if len(campaign_name) < 3:
        await message.answer(_("campaign-name-too-short"))
        return

    if len(campaign_name) > 100:
        await message.answer(_("campaign-name-too-long"))
        return

    # Сохраняем название и переходим к бюджету
    await state.update_data(name=campaign_name)
    await state.set_state(CreateCampaignStates.waiting_for_budget)

    text = _("create-campaign-enter-budget", name=campaign_name)

    await message.answer(text, reply_markup=get_create_campaign_cancel_keyboard())


@router.message(CreateCampaignStates.waiting_for_budget, AdvertiserFilter())
async def create_campaign_budget(message: Message, state: FSMContext):
    """Обработка бюджета кампании"""
    try:
        budget = Decimal(message.text.strip().replace(",", "."))

        if budget <= 0:
            await message.answer(_("budget-must-be-positive"))
            return

        if budget > 1000000:  # Максимальный бюджет 1 млн
            await message.answer(_("budget-too-large"))
            return

    except (ValueError, TypeError):
        await message.answer(_("invalid-budget-format"))
        return

    # Сохраняем бюджет и переходим к дате начала
    await state.update_data(budget=budget)
    await state.set_state(CreateCampaignStates.waiting_for_start_date)

    text = _("create-campaign-enter-start-date", budget=budget)

    await message.answer(text, reply_markup=get_start_date_keyboard())


@router.callback_query(
    F.data == "start_now", CreateCampaignStates.waiting_for_start_date
)
async def create_campaign_start_now(call: CallbackQuery, state: FSMContext):
    """Установка текущего времени как даты начала"""
    await call.answer()

    start_date = datetime.now()
    await state.update_data(start_date=start_date)
    await state.set_state(CreateCampaignStates.waiting_for_end_date)

    text = _(
        "create-campaign-enter-end-date",
        start_date=start_date.strftime("%d.%m.%Y %H:%M"),
    )

    await call.message.edit_text(text, reply_markup=get_end_date_keyboard())


@router.message(CreateCampaignStates.waiting_for_start_date, AdvertiserFilter())
async def create_campaign_start_date(message: Message, state: FSMContext):
    """Обработка даты начала кампании"""
    try:
        # Пытаемся распарсить дату в формате ДД.ММ.ГГГГ ЧЧ:ММ
        start_date = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")

        if start_date < datetime.now():
            await message.answer(_("start-date-in-past"))
            return

    except ValueError:
        await message.answer(_("invalid-date-format"))
        return

    await state.update_data(start_date=start_date)
    await state.set_state(CreateCampaignStates.waiting_for_end_date)

    text = _(
        "create-campaign-enter-end-date",
        start_date=start_date.strftime("%d.%m.%Y %H:%M"),
    )

    await message.answer(text, reply_markup=get_end_date_keyboard())


@router.callback_query(
    F.data == "end_one_week", CreateCampaignStates.waiting_for_end_date
)
async def create_campaign_end_one_week(call: CallbackQuery, state: FSMContext):
    """Установка даты окончания через неделю"""
    await call.answer()

    data = await state.get_data()
    start_date = data.get("start_date", datetime.now())
    end_date = start_date + timedelta(weeks=1)

    await create_campaign_confirm(call, state, end_date)


@router.callback_query(
    F.data == "end_one_month", CreateCampaignStates.waiting_for_end_date
)
async def create_campaign_end_one_month(call: CallbackQuery, state: FSMContext):
    """Установка даты окончания через месяц"""
    await call.answer()

    data = await state.get_data()
    start_date = data.get("start_date", datetime.now())
    end_date = start_date + timedelta(days=30)

    await create_campaign_confirm(call, state, end_date)


@router.message(CreateCampaignStates.waiting_for_end_date, AdvertiserFilter())
async def create_campaign_end_date(message: Message, state: FSMContext):
    """Обработка даты окончания кампании"""
    try:
        end_date = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")

        data = await state.get_data()
        start_date = data.get("start_date")

        if end_date <= start_date:
            await message.answer(_("end-date-before-start"))
            return

    except ValueError:
        await message.answer(_("invalid-date-format"))
        return

    await create_campaign_confirm(message, state, end_date)


async def create_campaign_confirm(
    message_or_call, state: FSMContext, end_date: datetime
):
    """Подтверждение создания кампании"""
    await state.update_data(end_date=end_date)
    await state.set_state(CreateCampaignStates.confirmation)

    data = await state.get_data()

    text = _(
        "create-campaign-confirmation",
        name=data["name"],
        budget=data["budget"],
        start_date=data["start_date"].strftime("%d.%m.%Y %H:%M"),
        end_date=end_date.strftime("%d.%m.%Y %H:%M"),
    )

    keyboard = get_campaign_confirmation_keyboard()

    if hasattr(message_or_call, "message"):
        await message_or_call.message.edit_text(text, reply_markup=keyboard)
    else:
        await message_or_call.answer(text, reply_markup=keyboard)


@router.callback_query(
    F.data == "confirm_create_campaign", CreateCampaignStates.confirmation
)
async def create_campaign_final(call: CallbackQuery, state: FSMContext, session):
    """Финальное создание кампании"""
    await call.answer()

    data = await state.get_data()

    try:
        campaign_service = AdCampaignService(session)

        campaign = await campaign_service.create_campaign(
            advertiser_id=data["advertiser_id"],
            name=data["name"],
            daily_budget=float(data["budget"]),
            start_date=data["start_date"],
            end_date=data["end_date"],
        )

        await state.clear()

        text = _(
            "campaign-created-success", name=campaign.name, campaign_id=campaign.id
        )

        keyboard = get_campaign_created_keyboard(campaign.id)
        await call.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        await state.clear()
        await call.message.edit_text(
            _("campaign-creation-error"), reply_markup=get_advertiser_menu()
        )


# Обработчик отмены создания кампании
@router.callback_query(
    AdCallbackFactory.filter(F.action == "ad_menu"), CreateCampaignStates()
)
async def cancel_campaign_creation(call: CallbackQuery, state: FSMContext):
    """Отмена создания кампании"""
    await call.answer()
    await state.clear()

    # Возвращаемся в меню рекламодателя
    from handlers.ads import advertiser_menu

    await advertiser_menu(call, call.bot.session)


# Хендлеры для админов
@router.callback_query(
    AdCallbackFactory.filter(F.action == "ad_menu" & F.role == "admin"), AdminFilter()
)
async def admin_ad_menu(call: CallbackQuery):
    """Админское меню рекламы"""
    await call.answer()

    text = _("admin-ad-menu")
    await call.message.edit_text(text, reply_markup=get_admin_ad_menu())


@router.callback_query(
    AdCallbackFactory.filter(F.action == "moderate_ads"), AdminFilter()
)
async def moderate_ads(call: CallbackQuery, session):
    """Модерация рекламных объявлений"""
    await call.answer()

    try:
        creative_service = AdCreativeService(session)
        pending_creatives = await creative_service.get_pending_moderation()

        text = _("moderation-queue-header")

        if not pending_creatives:
            text += "\n\n" + _("no-creatives-pending")
        else:
            text += f"\n\n📊 Всего креативов на модерации: {len(pending_creatives)}"

        keyboard = get_moderation_queue_keyboard(pending_creatives)
        await call.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        await call.message.edit_text(
            _("moderation-error"), reply_markup=get_admin_ad_menu()
        )


@router.callback_query(
    AdCallbackFactory.filter(F.action == "moderate_creative"), AdminFilter()
)
async def moderate_creative(
    call: CallbackQuery, callback_data: AdCallbackFactory, session
):
    """Просмотр конкретного креатива для модерации"""
    await call.answer()

    try:
        creative_service = AdCreativeService(session)
        creative = await creative_service.get_creative(callback_data.item_id)

        if not creative:
            await call.message.edit_text(
                _("creative-not-found"), reply_markup=get_moderation_queue_keyboard()
            )
            return

        # Формируем детальную информацию о креативе
        text = _("creative-details-header")
        text += "\n\n"
        text += _("creative-type", type=creative.creative_type) + "\n"
        text += (
            _(
                "creative-campaign",
                campaign=creative.campaign.name if creative.campaign else "Unknown",
            )
            + "\n"
        )

        if creative.campaign and creative.campaign.advertiser:
            advertiser_name = f"ID: {creative.campaign.advertiser.user_id}"
            text += _("creative-advertiser", advertiser=advertiser_name) + "\n"

        text += (
            _("creative-created", date=creative.created_at.strftime("%d.%m.%Y %H:%M"))
            + "\n"
        )

        # Добавляем контент креатива если есть
        if hasattr(creative, "content") and creative.content:
            text += f"\n📝 Контент:\n{creative.content[:200]}{'...' if len(creative.content) > 200 else ''}"

        keyboard = get_creative_moderation_keyboard(creative.id)
        await call.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        await call.message.edit_text(
            _("moderation-error"), reply_markup=get_moderation_queue_keyboard()
        )


@router.callback_query(
    AdCallbackFactory.filter(F.action == "approve_creative"), AdminFilter()
)
async def approve_creative(
    call: CallbackQuery, callback_data: AdCallbackFactory, session
):
    """Одобрение креатива"""
    await call.answer()

    try:
        from database.models.ad import CreativeStatus

        creative_service = AdCreativeService(session)
        creative = await creative_service.moderate_creative(
            callback_data.item_id, CreativeStatus.APPROVED
        )

        if creative:
            await call.message.edit_text(
                _("creative-approved-success"),
                reply_markup=get_moderation_queue_keyboard(),
            )

            # Возвращаемся к очереди модерации
            await moderate_ads(call, session)
        else:
            await call.message.edit_text(
                _("creative-not-found"), reply_markup=get_moderation_queue_keyboard()
            )

    except Exception as e:
        await call.message.edit_text(
            _("moderation-error"), reply_markup=get_moderation_queue_keyboard()
        )


@router.callback_query(
    AdCallbackFactory.filter(F.action == "reject_creative"), AdminFilter()
)
async def reject_creative(call: CallbackQuery, callback_data: AdCallbackFactory):
    """Отклонение креатива - выбор причины"""
    await call.answer()

    text = _("select-rejection-reason")
    keyboard = get_rejection_reason_keyboard(callback_data.item_id)

    await call.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(
    AdCallbackFactory.filter(F.action == "reject_reason"), AdminFilter()
)
async def reject_creative_with_reason(
    call: CallbackQuery, callback_data: AdCallbackFactory, session
):
    """Отклонение креатива с предустановленной причиной"""
    await call.answer()

    try:
        from database.models.ad import CreativeStatus

        # Маппинг причин
        reason_map = {
            "inappropriate": _("reason-inappropriate"),
            "misleading": _("reason-misleading"),
            "quality": _("reason-quality"),
            "policy": _("reason-policy"),
        }

        reason = reason_map.get(callback_data.extra, _("reason-policy"))

        creative_service = AdCreativeService(session)
        creative = await creative_service.moderate_creative(
            callback_data.item_id, CreativeStatus.REJECTED, reason
        )

        if creative:
            await call.message.edit_text(
                _("creative-rejected-success", reason=reason),
                reply_markup=get_moderation_queue_keyboard(),
            )

            # Возвращаемся к очереди модерации
            await moderate_ads(call, session)
        else:
            await call.message.edit_text(
                _("creative-not-found"), reply_markup=get_moderation_queue_keyboard()
            )

    except Exception as e:
        await call.message.edit_text(
            _("moderation-error"), reply_markup=get_moderation_queue_keyboard()
        )


# FSM для кастомной причины отклонения
class CustomRejectionStates(StatesGroup):
    waiting_for_reason = State()


@router.callback_query(
    AdCallbackFactory.filter(F.action == "reject_custom"), AdminFilter()
)
async def reject_creative_custom(
    call: CallbackQuery, callback_data: AdCallbackFactory, state: FSMContext
):
    """Отклонение креатива с кастомной причиной"""
    await call.answer()

    await state.update_data(creative_id=callback_data.item_id)
    await state.set_state(CustomRejectionStates.waiting_for_reason)

    text = _("enter-custom-reason")
    keyboard = get_creative_moderation_keyboard(callback_data.item_id)

    await call.message.edit_text(text, reply_markup=keyboard)


@router.message(CustomRejectionStates.waiting_for_reason, AdminFilter())
async def process_custom_rejection_reason(message: Message, state: FSMContext, session):
    """Обработка кастомной причины отклонения"""
    try:
        from database.models.ad import CreativeStatus

        data = await state.get_data()
        creative_id = data.get("creative_id")
        custom_reason = message.text.strip()

        if not custom_reason:
            await message.answer(_("enter-custom-reason"))
            return

        creative_service = AdCreativeService(session)
        creative = await creative_service.moderate_creative(
            creative_id, CreativeStatus.REJECTED, custom_reason
        )

        await state.clear()

        if creative:
            await message.answer(
                _("creative-rejected-success", reason=custom_reason),
                reply_markup=get_moderation_queue_keyboard(),
            )
        else:
            await message.answer(
                _("creative-not-found"), reply_markup=get_moderation_queue_keyboard()
            )

    except Exception as e:
        await state.clear()
        await message.answer(
            _("moderation-error"), reply_markup=get_moderation_queue_keyboard()
        )


@router.callback_query(
    AdCallbackFactory.filter(F.action == "all_campaigns"), AdminFilter()
)
async def all_campaigns(call: CallbackQuery, callback_data: AdCallbackFactory, session):
    """Все рекламные кампании (админ)"""
    await call.answer()

    try:
        # Получаем страницу из callback_data (по умолчанию 1)
        page = callback_data.item_id if callback_data.item_id else 1

        # Получаем все кампании
        campaign_service = AdCampaignService(session)
        campaigns = await campaign_service.get_all_campaigns()

        if not campaigns:
            await call.message.edit_text(
                _("no-campaigns-found"), reply_markup=get_admin_ad_menu()
            )
            return

        # Пагинация
        campaigns_per_page = 10
        start_idx = (page - 1) * campaigns_per_page
        end_idx = start_idx + campaigns_per_page
        page_campaigns = campaigns[start_idx:end_idx]

        # Формируем текст сообщения
        text = _("all-campaigns-title") + "\n\n"
        text += _("total-campaigns").format(count=len(campaigns)) + "\n"
        text += _("page-info").format(
            current=page,
            total=(len(campaigns) + campaigns_per_page - 1) // campaigns_per_page,
        )

        await call.message.edit_text(
            text, reply_markup=get_all_campaigns_keyboard(page_campaigns, page)
        )

    except Exception as e:
        logger.error(f"Error in all_campaigns: {e}")
        await call.answer(_("error-occurred"), show_alert=True)
        await call.message.edit_text(
            _("error-occurred"), reply_markup=get_admin_ad_menu()
        )


@router.callback_query(
    AdCallbackFactory.filter(F.action == "view_advertiser_details"), AdminFilter()
)
async def view_advertiser_details(
    call: CallbackQuery, callback_data: AdCallbackFactory, session
):
    """Просмотр деталей рекламодателя"""
    await call.answer()

    try:
        advertiser_service = AdvertiserService(session)
        advertiser = await advertiser_service.get_advertiser_by_id(
            callback_data.item_id
        )

        if not advertiser:
            await call.message.edit_text(
                _("advertiser_not_found"), reply_markup=get_admin_ad_menu()
            )
            return

        # Получаем статистику рекламодателя
        campaign_service = AdCampaignService(session)
        campaigns = await campaign_service.get_campaigns_by_advertiser(advertiser.id)

        total_campaigns = len(campaigns)
        active_campaigns = len([c for c in campaigns if c.status == "active"])
        total_spent = sum(c.spent_amount for c in campaigns)

        # Формируем детальную информацию
        text = _("advertiser_details").format(
            name=advertiser.name,
            balance=advertiser.balance,
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            total_spent=total_spent,
            created_at=advertiser.created_at.strftime("%d.%m.%Y %H:%M"),
        )

        # Создаем клавиатуру с действиями
        keyboard = get_advertiser_details_keyboard(advertiser.id)

        await call.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in view_advertiser_details: {e}")
        await call.answer(_("error-occurred"), show_alert=True)
        await call.message.edit_text(
            _("error-occurred"), reply_markup=get_admin_ad_menu()
        )


@router.callback_query(
    AdCallbackFactory.filter(F.action == "advertiser_management"), AdminFilter()
)
async def advertiser_management(
    call: CallbackQuery, callback_data: AdCallbackFactory, session
):
    """Управление рекламодателями"""
    await call.answer()

    try:
        # Получаем страницу из callback_data (по умолчанию 1)
        page = callback_data.item_id if callback_data.item_id else 1

        # Получаем всех рекламодателей
        advertiser_service = AdvertiserService(session)
        advertisers = await advertiser_service.get_all_advertisers()

        if not advertisers:
            await call.message.edit_text(
                _("no-advertisers-found"), reply_markup=get_admin_ad_menu()
            )
            return

        # Пагинация
        advertisers_per_page = 10
        total_pages = (
            len(advertisers) + advertisers_per_page - 1
        ) // advertisers_per_page
        start_idx = (page - 1) * advertisers_per_page
        end_idx = start_idx + advertisers_per_page
        page_advertisers = advertisers[start_idx:end_idx]

        # Формируем текст сообщения
        text = _("advertisers-management-title") + "\n\n"
        text += _("total-advertisers").format(count=len(advertisers)) + "\n"
        text += _("advertisers-page-info").format(
            current=page,
            total=total_pages,
        )

        await call.message.edit_text(
            text,
            reply_markup=get_all_advertisers_keyboard(
                page_advertisers, page, total_pages
            ),
        )

    except Exception as e:
        logger.error(f"Error in advertiser_management: {e}")
        await call.answer(_("error-occurred"), show_alert=True)
        await call.message.edit_text(
            _("error-occurred"), reply_markup=get_admin_ad_menu()
        )
