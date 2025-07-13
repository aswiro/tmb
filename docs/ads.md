# Database Schema for Advertising System

## 1. advertisers (Advertisers)
Stores information about advertising clients.

- **id** (PK): Unique advertiser ID
- **user_id** (FK): Telegram user ID (references users.id)
- **company_name**: Company name or advertiser name
- **balance**: Current monetary balance
- **created_at**: Registration date

## 2. ad_campaigns (Advertising Campaigns)
Each record represents an individual advertising order.

- **id** (PK): Unique campaign ID
- **advertiser_id** (FK): Reference to advertisers.id
- **name**: Campaign name (e.g. "New Year Sale 2024")
- **budget**: Total budget allocated for this campaign
- **spent_amount**: Amount already spent from budget
- **start_date**: Display start date
- **end_date**: Display end date
- **status**: Campaign status (draft, active, paused, completed, archived)
- **created_at**: Campaign creation date

## 3. ad_creatives (Ad Creatives)
Stores advertising content. One campaign can have multiple creative variants for A/B testing.

- **id** (PK): Unique creative ID
- **campaign_id** (FK): Reference to ad_campaigns.id
- **content_type**: Content type (text, photo, video)
- **text**: Ad text
- **file_id**: Telegram file_id for photo or video
- **url**: Link (if any)
- **created_at**: Creation date
- **status**: Moderation status ('pending', 'approved', 'rejected')
- **moderator_id**: ID of moderator who reviewed (links to users/moderators table)
- **moderation_comment**: Moderator comment (e.g. rejection reason)

## 4. ad_placements (Ad Placements)
Indicates which groups to show ads for specific campaigns.

- **id** (PK): Unique ID
- **campaign_id** (FK): Reference to ad_campaigns.id
- **group_id** (FK): Reference to groups.id

## 5. ad_analytics (Display Analytics)
Important analytics table storing raw event data.

- **id** (PK): Unique event ID
- **creative_id** (FK): Reference to ad_creatives.id
- **group_id** (FK): Group where display occurred
- **user_id** (FK): User who saw the ad
- **event_type**: Event type (impression - view, click - click)
- **event_time**: Exact event time

## 6. transactions (Balance History)
Allows advertisers to track their spending.

- **id** (PK): Unique transaction ID
- **advertiser_id** (FK): Reference to advertisers.id
- **amount**: Transaction amount (positive for deposits, negative for ad charges)
- **type**: Type (deposit - add funds, spend - charge for view/click)
- **description**: Description (e.g. "Charge for campaign #123")
- **created_at**: Transaction date

---

# Service Layer Documentation

## AdvertiserService

Сервис для работы с рекламодателями. Управляет созданием, обновлением и балансом рекламодателей.

### Methods:

#### `create_advertiser(user_id: int, name: str) -> Advertiser`
- **Назначение**: Создание нового рекламодателя
- **Параметры**:
  - `user_id`: ID пользователя Telegram
  - `name`: Имя рекламодателя или компании
- **Возвращает**: Объект Advertiser с начальным балансом 0.00
- **Использование**: Регистрация нового рекламодателя в системе

#### `get_advertiser(user_id: int) -> Advertiser | None`
- **Назначение**: Получение рекламодателя по ID пользователя
- **Параметры**:
  - `user_id`: ID пользователя Telegram
- **Возвращает**: Объект Advertiser или None, если не найден
- **Использование**: Поиск существующего рекламодателя

#### `update_advertiser(advertiser_id: int, **kwargs) -> Advertiser | None`
- **Назначение**: Обновление данных рекламодателя
- **Параметры**:
  - `advertiser_id`: ID рекламодателя
  - `**kwargs**: Поля для обновления
- **Возвращает**: Обновленный объект Advertiser или None
- **Использование**: Изменение информации о рекламодателе

#### `add_balance(user_id: int, amount: Decimal) -> Advertiser | None`
- **Назначение**: Пополнение баланса рекламодателя
- **Параметры**:
  - `user_id`: ID пользователя Telegram
  - `amount`: Сумма пополнения
- **Возвращает**: Обновленный объект Advertiser или None
- **Использование**: Добавление средств на счет рекламодателя

#### `deduct_balance(user_id: int, amount: Decimal) -> bool`
- **Назначение**: Списание средств с баланса рекламодателя
- **Параметры**:
  - `user_id`: ID пользователя Telegram
  - `amount`: Сумма списания
- **Возвращает**: True при успешном списании, False при недостатке средств
- **Использование**: Оплата рекламных показов и кликов

## AdCampaignService

Сервис для работы с рекламными кампаниями. Управляет жизненным циклом кампаний.

### Methods:

#### `create_campaign(advertiser_id: int, name: str, daily_budget: float, **kwargs) -> AdCampaign`
- **Назначение**: Создание новой рекламной кампании
- **Параметры**:
  - `advertiser_id`: ID рекламодателя
  - `name`: Название кампании
  - `daily_budget`: Дневной бюджет
  - `**kwargs`: Дополнительные параметры кампании
- **Возвращает**: Объект AdCampaign со статусом DRAFT
- **Использование**: Создание новой рекламной кампании

#### `update_campaign_status(campaign_id: int, status: CampaignStatus) -> AdCampaign | None`
- **Назначение**: Обновление статуса рекламной кампании
- **Параметры**:
  - `campaign_id`: ID кампании
  - `status`: Новый статус (DRAFT, ACTIVE, PAUSED, COMPLETED, ARCHIVED)
- **Возвращает**: Обновленный объект AdCampaign или None
- **Использование**: Управление состоянием кампании

#### `get_campaign(campaign_id: int) -> AdCampaign | None`
- **Назначение**: Получение рекламной кампании по ID
- **Параметры**:
  - `campaign_id`: ID кампании
- **Возвращает**: Объект AdCampaign или None
- **Использование**: Получение информации о конкретной кампании

#### `get_advertiser_campaigns(advertiser_id: int, status: CampaignStatus = None) -> list[AdCampaign]`
- **Назначение**: Получение всех кампаний рекламодателя
- **Параметры**:
  - `advertiser_id`: ID рекламодателя
  - `status`: Фильтр по статусу (опционально)
- **Возвращает**: Список объектов AdCampaign
- **Использование**: Просмотр всех кампаний рекламодателя

#### `update_campaign(campaign_id: int, **kwargs) -> AdCampaign | None`
- **Назначение**: Обновление данных рекламной кампании
- **Параметры**:
  - `campaign_id`: ID кампании
  - `**kwargs`: Поля для обновления
- **Возвращает**: Обновленный объект AdCampaign или None
- **Использование**: Изменение параметров кампании

## AdCreativeService

Сервис для работы с рекламными креативами. Управляет контентом и модерацией.

### Methods:

#### `create_creative(campaign_id: int, content: str, **kwargs) -> AdCreative`
- **Назначение**: Создание нового рекламного креатива
- **Параметры**:
  - `campaign_id`: ID кампании
  - `content`: Содержимое креатива
  - `**kwargs`: Дополнительные параметры (file_id, url и т.д.)
- **Возвращает**: Объект AdCreative со статусом PENDING
- **Использование**: Добавление рекламного контента к кампании

#### `moderate_creative(creative_id: int, status: CreativeStatus, rejection_reason: str = None) -> AdCreative | None`
- **Назначение**: Модерация рекламного креатива
- **Параметры**:
  - `creative_id`: ID креатива
  - `status`: Результат модерации (APPROVED, REJECTED)
  - `rejection_reason`: Причина отклонения (для REJECTED)
- **Возвращает**: Обновленный объект AdCreative или None
- **Использование**: Процесс модерации рекламного контента

#### `get_creative(creative_id: int) -> AdCreative | None`
- **Назначение**: Получение рекламного креатива по ID
- **Параметры**:
  - `creative_id`: ID креатива
- **Возвращает**: Объект AdCreative или None
- **Использование**: Получение информации о конкретном креативе

#### `get_campaign_creatives(campaign_id: int, status: CreativeStatus = None) -> list[AdCreative]`
- **Назначение**: Получение всех креативов кампании
- **Параметры**:
  - `campaign_id`: ID кампании
  - `status`: Фильтр по статусу (опционально)
- **Возвращает**: Список объектов AdCreative
- **Использование**: Просмотр всех креативов в кампании

#### `get_pending_moderation() -> list[AdCreative]`
- **Назначение**: Получение всех креативов, ожидающих модерации
- **Параметры**: Нет
- **Возвращает**: Список объектов AdCreative со статусом PENDING
- **Использование**: Получение очереди на модерацию для администраторов

## AdPlacementService

Сервис для работы с размещениями рекламы. Управляет привязкой кампаний к группам.

### Methods:

#### `create_placement(campaign_id: int, group_id: int, **kwargs) -> AdPlacement`
- **Назначение**: Создание нового размещения рекламы
- **Параметры**:
  - `campaign_id`: ID кампании
  - `group_id`: ID группы для размещения
  - `**kwargs`: Дополнительные параметры размещения
- **Возвращает**: Объект AdPlacement
- **Использование**: Привязка кампании к конкретной группе

#### `delete_placement(placement_id: int) -> bool`
- **Назначение**: Удаление размещения рекламы
- **Параметры**:
  - `placement_id`: ID размещения
- **Возвращает**: True при успешном удалении, False если размещение не найдено
- **Использование**: Отключение показа рекламы в группе

#### `get_campaign_placements(campaign_id: int) -> list[AdPlacement]`
- **Назначение**: Получение всех размещений кампании
- **Параметры**:
  - `campaign_id`: ID кампании
- **Возвращает**: Список объектов AdPlacement
- **Использование**: Просмотр всех групп, где размещена кампания

#### `get_group_placements(group_id: int) -> list[AdPlacement]`
- **Назначение**: Получение всех размещений в группе
- **Параметры**:
  - `group_id`: ID группы
- **Возвращает**: Список объектов AdPlacement
- **Использование**: Просмотр всех кампаний, размещенных в группе

## AdAnalyticsService

Сервис для работы с аналитикой рекламы. Собирает статистику показов и кликов.

### Methods:

#### `record_event(creative_id: int, event_type: AdEventType, user_id: int = None) -> AdEvent`
- **Назначение**: Запись события рекламы (показ, клик и т.д.)
- **Параметры**:
  - `creative_id`: ID креатива
  - `event_type`: Тип события (IMPRESSION, CLICK)
  - `user_id`: ID пользователя (опционально)
- **Возвращает**: Объект AdEvent
- **Использование**: Фиксация взаимодействий пользователей с рекламой

#### `get_creative_stats(creative_id: int, days: int = 30) -> dict`
- **Назначение**: Получение статистики по креативу
- **Параметры**:
  - `creative_id`: ID креатива
  - `days`: Период для анализа (по умолчанию 30 дней)
- **Возвращает**: Словарь с ключами:
  - `impressions`: Количество показов
  - `clicks`: Количество кликов
  - `ctr`: CTR (Click-Through Rate) в процентах
- **Использование**: Анализ эффективности конкретного креатива

#### `get_campaign_stats(campaign_id: int, days: int = 30) -> dict`
- **Назначение**: Получение статистики по кампании
- **Параметры**:
  - `campaign_id`: ID кампании
  - `days`: Период для анализа (по умолчанию 30 дней)
- **Возвращает**: Словарь с ключами:
  - `impressions`: Общее количество показов
  - `clicks`: Общее количество кликов
  - `ctr`: Средний CTR по кампании
  - `spent`: Потраченная сумма
- **Использование**: Анализ общей эффективности кампании

---

# Workflow Examples

## Создание и запуск рекламной кампании

1. **Регистрация рекламодателя**: `AdvertiserService.create_advertiser()`
2. **Пополнение баланса**: `AdvertiserService.add_balance()`
3. **Создание кампании**: `AdCampaignService.create_campaign()`
4. **Добавление креативов**: `AdCreativeService.create_creative()`
5. **Модерация контента**: `AdCreativeService.moderate_creative()`
6. **Настройка размещений**: `AdPlacementService.create_placement()`
7. **Запуск кампании**: `AdCampaignService.update_campaign_status(status=ACTIVE)`

## Отслеживание эффективности

1. **Запись событий**: `AdAnalyticsService.record_event()` при каждом показе/клике
2. **Анализ креативов**: `AdAnalyticsService.get_creative_stats()`
3. **Анализ кампаний**: `AdAnalyticsService.get_campaign_stats()`
4. **Списание средств**: `AdvertiserService.deduct_balance()` за клики
