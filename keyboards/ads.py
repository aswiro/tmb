from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from keyboards.buttons import (
    AdCallbackFactory,
    get_admin_back_to_menu,
    get_user_back_to_menu,
)


def get_advertiser_menu() -> InlineKeyboardMarkup:
    """Клавиатура меню рекламодателя"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("my-campaigns"),
                callback_data=AdCallbackFactory(action="my_campaigns").pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("create-campaign"),
                callback_data=AdCallbackFactory(action="create_campaign").pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("my-balance"),
                callback_data=AdCallbackFactory(action="balance").pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("ad-analytics"),
                callback_data=AdCallbackFactory(action="analytics").pack(),
            )
        ],
        [get_user_back_to_menu()],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_advertiser_details_keyboard(advertiser_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для деталей рекламодателя"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("edit_advertiser_balance"),
                callback_data=AdCallbackFactory(
                    action="edit_advertiser_balance",
                    item_id=advertiser_id,
                    role="admin"
                ).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=_("view_advertiser_campaigns"),
                callback_data=AdCallbackFactory(
                    action="view_advertiser_campaigns",
                    item_id=advertiser_id,
                    role="admin"
                ).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=_("block_advertiser"),
                callback_data=AdCallbackFactory(
                    action="block_advertiser",
                    item_id=advertiser_id,
                    role="admin"
                ).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back_to_advertisers"),
                callback_data=AdCallbackFactory(
                    action="advertiser_management",
                    role="admin"
                ).pack()
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_no_campaigns_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура когда у рекламодателя нет кампаний"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("create-campaign"),
                callback_data=AdCallbackFactory(action="create_campaign").pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back-to-ad-menu"),
                callback_data=AdCallbackFactory(action="ad_menu").pack(),
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_my_campaigns_keyboard(campaigns=None, page=1) -> InlineKeyboardMarkup:
    """Клавиатура для списка кампаний рекламодателя"""
    keyboard = []
    
    # Добавляем кнопки для каждой кампании
    if campaigns:
        for campaign in campaigns[:10]:  # Ограничиваем до 10 кампаний на страницу
            # Определяем эмодзи статуса
            status_emoji = {
                "draft": "📝",
                "active": "✅",
                "paused": "⏸️",
                "completed": "✔️",
                "archived": "📦",
            }.get(campaign.status.value, "❓")
            
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"{status_emoji} {campaign.name[:20]}{'...' if len(campaign.name) > 20 else ''}",
                        callback_data=AdCallbackFactory(
                            action="campaign_details", item_id=campaign.id
                        ).pack(),
                    )
                ]
            )
    
    # Добавляем кнопки управления
    control_buttons = [
        InlineKeyboardButton(
            text=_("create-campaign"),
            callback_data=AdCallbackFactory(action="create_campaign").pack(),
        ),
        InlineKeyboardButton(
            text=_("campaign-analytics"),
            callback_data=AdCallbackFactory(action="campaigns_analytics").pack(),
        ),
    ]
    keyboard.append(control_buttons)
    
    # Если кампаний больше 10, добавляем пагинацию
    if campaigns and len(campaigns) > 10:
        pagination_buttons = [
            InlineKeyboardButton(
                text=_("show-more-campaigns"),
                callback_data=AdCallbackFactory(
                    action="campaigns_page",
                    item_id=page + 1,
                ).pack(),
            )
        ]
        keyboard.append(pagination_buttons)
    
    # Кнопка возврата
    keyboard.append(
        [
            InlineKeyboardButton(
                text=_("back-to-ad-menu"),
                callback_data=AdCallbackFactory(action="ad_menu").pack(),
            )
        ]
    )
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_campaign_details_keyboard(campaign) -> InlineKeyboardMarkup:
    """Клавиатура для детальной информации о кампании"""
    keyboard = []
    
    # Кнопки в зависимости от статуса
    if campaign.status.value == "draft":
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=_("activate-campaign"),
                    callback_data=AdCallbackFactory(
                        action="activate_campaign", item_id=campaign.id
                    ).pack(),
                )
            ]
        )
    elif campaign.status.value == "active":
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=_("pause-campaign"),
                    callback_data=AdCallbackFactory(
                        action="pause_campaign", item_id=campaign.id
                    ).pack(),
                )
            ]
        )
    elif campaign.status.value == "paused":
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=_("resume-campaign"),
                    callback_data=AdCallbackFactory(
                        action="resume_campaign", item_id=campaign.id
                    ).pack(),
                )
            ]
        )
    
    # Общие кнопки управления
    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    text=_("edit-campaign"),
                    callback_data=AdCallbackFactory(
                        action="edit_campaign", item_id=campaign.id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=_("campaign-creatives"),
                    callback_data=AdCallbackFactory(
                        action="campaign_creatives", item_id=campaign.id
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_("campaign-analytics"),
                    callback_data=AdCallbackFactory(
                        action="campaign_analytics", item_id=campaign.id
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("back-to-campaigns"),
                    callback_data=AdCallbackFactory(action="my_campaigns").pack(),
                )
            ],
        ]
    )
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_create_campaign_cancel_keyboard():
    """Клавиатура с кнопкой отмены для создания кампании"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_("cancel"),
            callback_data=AdCallbackFactory(action="ad_menu").pack()
        )]
    ])


def get_start_date_keyboard():
    """Клавиатура для выбора даты начала кампании"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_("start-now"),
            callback_data="start_now"
        )],
        [InlineKeyboardButton(
            text=_("cancel"),
            callback_data=AdCallbackFactory(action="ad_menu").pack()
        )]
    ])


def get_end_date_keyboard():
    """Клавиатура для выбора даты окончания кампании"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_("one-week"),
            callback_data="end_one_week"
        )],
        [InlineKeyboardButton(
            text=_("one-month"),
            callback_data="end_one_month"
        )],
        [InlineKeyboardButton(
            text=_("cancel"),
            callback_data=AdCallbackFactory(action="ad_menu").pack()
        )]
    ])


def get_campaign_confirmation_keyboard():
    """Клавиатура для подтверждения создания кампании"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_("confirm-create"),
            callback_data="confirm_create_campaign"
        )],
        [InlineKeyboardButton(
            text=_("cancel"),
            callback_data=AdCallbackFactory(action="ad_menu").pack()
        )]
    ])


def get_campaign_created_keyboard(campaign_id):
    """Клавиатура после успешного создания кампании"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=_("view-campaign"),
            callback_data=AdCallbackFactory(
                action="campaign_details", 
                item_id=campaign_id
            ).pack()
        )],
        [InlineKeyboardButton(
            text=_("my-campaigns"),
            callback_data=AdCallbackFactory(action="my_campaigns").pack()
        )],
        [InlineKeyboardButton(
            text=_("back-to-ad-menu"),
            callback_data=AdCallbackFactory(action="ad_menu").pack()
        )]
    ])


def get_admin_ad_menu() -> InlineKeyboardMarkup:
    """Клавиатура админского меню рекламы"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("moderate-ads"),
                callback_data=AdCallbackFactory(
                    action="moderate_ads", role="admin"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("all-campaigns"),
                callback_data=AdCallbackFactory(
                    action="all_campaigns", role="admin"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("advertiser-management"),
                callback_data=AdCallbackFactory(
                    action="advertiser_management", role="admin"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("ad-analytics-admin"),
                callback_data=AdCallbackFactory(
                    action="analytics_admin", role="admin"
                ).pack(),
            )
        ],
        [get_admin_back_to_menu()],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_moderation_queue_keyboard(creatives=None, page=1) -> InlineKeyboardMarkup:
    """Клавиатура для очереди модерации креативов"""
    keyboard = []
    
    # Добавляем кнопки для каждого креатива на модерации
    if creatives:
        for creative in creatives[:10]:  # Ограничиваем до 10 креативов на страницу
            # Получаем информацию о кампании
            campaign_name = creative.campaign.name if creative.campaign else "Unknown"
            
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"📝 {campaign_name[:15]}{'...' if len(campaign_name) > 15 else ''} - {creative.creative_type}",
                        callback_data=AdCallbackFactory(
                            action="moderate_creative", item_id=creative.id, role="admin"
                        ).pack(),
                    )
                ]
            )
    
    # Если креативов нет
    if not creatives:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=_("no-pending-creatives"),
                    callback_data="dummy"
                )
            ]
        )
    
    # Если креативов больше 10, добавляем пагинацию
    if creatives and len(creatives) > 10:
        pagination_buttons = [
            InlineKeyboardButton(
                text=_("show-more-creatives"),
                callback_data=AdCallbackFactory(
                    action="moderation_page",
                    item_id=page + 1,
                    role="admin"
                ).pack(),
            )
        ]
        keyboard.append(pagination_buttons)
    
    # Кнопка обновления и возврата
    keyboard.extend([
        [
            InlineKeyboardButton(
                text=_("refresh-queue"),
                callback_data=AdCallbackFactory(
                    action="moderate_ads", role="admin"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back-to-admin-menu"),
                callback_data=AdCallbackFactory(
                    action="admin_ad_menu", role="admin"
                ).pack(),
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_creative_moderation_keyboard(creative_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для модерации конкретного креатива"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("approve-creative"),
                callback_data=AdCallbackFactory(
                    action="approve_creative", item_id=creative_id, role="admin"
                ).pack(),
            ),
            InlineKeyboardButton(
                text=_("reject-creative"),
                callback_data=AdCallbackFactory(
                    action="reject_creative", item_id=creative_id, role="admin"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("view-campaign"),
                callback_data=AdCallbackFactory(
                    action="view_creative_campaign", item_id=creative_id, role="admin"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back-to-moderation"),
                callback_data=AdCallbackFactory(
                    action="moderate_ads", role="admin"
                ).pack(),
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_rejection_reason_keyboard(creative_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора причины отклонения креатива"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=_("inappropriate-content"),
                callback_data=AdCallbackFactory(
                    action="reject_reason", item_id=creative_id, role="admin", extra="inappropriate"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("misleading-info"),
                callback_data=AdCallbackFactory(
                    action="reject_reason", item_id=creative_id, role="admin", extra="misleading"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("poor-quality"),
                callback_data=AdCallbackFactory(
                    action="reject_reason", item_id=creative_id, role="admin", extra="quality"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("policy-violation"),
                callback_data=AdCallbackFactory(
                    action="reject_reason", item_id=creative_id, role="admin", extra="policy"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("custom-reason"),
                callback_data=AdCallbackFactory(
                    action="reject_custom", item_id=creative_id, role="admin"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=_("back-to-creative"),
                callback_data=AdCallbackFactory(
                    action="moderate_creative", item_id=creative_id, role="admin"
                ).pack(),
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_all_campaigns_keyboard(campaigns, page=1, total_pages=1) -> InlineKeyboardMarkup:
    """Клавиатура для отображения всех кампаний с пагинацией"""
    keyboard = []
    
    # Добавляем кнопки для каждой кампании на странице
    for campaign in campaigns:
        # Определяем эмодзи статуса
        status_emoji = {
            "active": "🟢",
            "paused": "⏸️", 
            "completed": "✅",
            "draft": "📝",
            "pending": "⏳"
        }.get(campaign.status, "❓")
        
        # Получаем имя рекламодателя
        advertiser_name = campaign.advertiser.name if campaign.advertiser else "Unknown"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {campaign.name[:20]}{'...' if len(campaign.name) > 20 else ''} | {advertiser_name[:15]}{'...' if len(advertiser_name) > 15 else ''}",
                callback_data=AdCallbackFactory(
                    action="view_campaign_details",
                    item_id=campaign.id,
                    role="admin"
                ).pack()
            )
        ])
    
    # Добавляем навигацию если есть несколько страниц
    if total_pages > 1:
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=AdCallbackFactory(
                        action="all_campaigns",
                        item_id=page - 1,
                        role="admin"
                    ).pack()
                )
            )
        
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=AdCallbackFactory(
                        action="all_campaigns",
                        item_id=page + 1,
                        role="admin"
                    ).pack()
                )
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    # Кнопка возврата в админское меню
    keyboard.append([
        InlineKeyboardButton(
            text=_("back-to-admin-menu"),
            callback_data=AdCallbackFactory(
                action="admin_ad_menu",
                role="admin"
            ).pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_all_advertisers_keyboard(advertisers, page=1, total_pages=1) -> InlineKeyboardMarkup:
    """Клавиатура для отображения всех рекламодателей с пагинацией"""
    keyboard = []
    
    # Добавляем кнопки для каждого рекламодателя на странице
    for advertiser in advertisers:
        # Определяем статус по балансу
        balance_emoji = "💰" if advertiser.balance > 0 else "💸"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{balance_emoji} {advertiser.name[:25]}{'...' if len(advertiser.name) > 25 else ''} | {advertiser.balance}₽",
                callback_data=AdCallbackFactory(
                    action="view_advertiser_details",
                    item_id=advertiser.id,
                    role="admin"
                ).pack()
            )
        ])
    
    # Добавляем навигацию если есть несколько страниц
    if total_pages > 1:
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=AdCallbackFactory(
                        action="advertiser_management",
                        item_id=page - 1,
                        role="admin"
                    ).pack()
                )
            )
        
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=AdCallbackFactory(
                        action="advertiser_management",
                        item_id=page + 1,
                        role="admin"
                    ).pack()
                )
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    # Кнопка возврата в админское меню
    keyboard.append([
        InlineKeyboardButton(
            text=_("back-to-admin-menu"),
            callback_data=AdCallbackFactory(
                action="admin_ad_menu",
                role="admin"
            ).pack()
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
