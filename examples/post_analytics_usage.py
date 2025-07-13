# examples/post_analytics_usage.py
"""
Примеры использования PostAnalyticsService
"""

import asyncio
from datetime import datetime, timedelta

from database import get_session
from database.unit_of_work import UnitOfWork
from database.models import PostStatus


async def track_post_interactions():
    """Пример отслеживания взаимодействий с постом"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        post_id = 1
        group_id = -1001234567890
        
        # Отслеживание просмотра
        await uow.post_analytics_service.track_view(post_id, group_id)
        print(f"Просмотр поста {post_id} в группе {group_id} отслежен")
        
        # Отслеживание клика
        await uow.post_analytics_service.track_click(post_id, group_id)
        print(f"Клик по посту {post_id} в группе {group_id} отслежен")
        
        # Отслеживание репоста
        await uow.post_analytics_service.track_share(post_id, group_id)
        print(f"Репост поста {post_id} в группе {group_id} отслежен")
        
        # Отслеживание реакций
        await uow.post_analytics_service.track_reaction(post_id, group_id, "👍")
        await uow.post_analytics_service.track_reaction(post_id, group_id, "❤️")
        await uow.post_analytics_service.track_reaction(post_id, group_id, "👍")  # Еще один лайк
        print(f"Реакции на пост {post_id} в группе {group_id} отслежены")
        
        # Отслеживание времени просмотра (в секундах)
        await uow.post_analytics_service.track_view_duration(post_id, group_id, 45)
        print(f"Время просмотра поста {post_id} в группе {group_id} отслежено")
        
        await uow.commit()


async def get_post_analytics_example():
    """Пример получения аналитики по посту"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        post_id = 1
        
        # Получаем аналитику по посту
        analytics = await uow.post_analytics_service.get_post_analytics(post_id)
        
        print(f"\n=== Аналитика поста {post_id} ===")
        print(f"Всего просмотров: {analytics['total_views']}")
        print(f"Всего кликов: {analytics['total_clicks']}")
        print(f"Всего репостов: {analytics['total_shares']}")
        print(f"Реакции: {analytics['total_reactions']}")
        print(f"Средний CTR: {analytics['average_ctr']}%")
        print(f"Средняя вовлеченность: {analytics['average_engagement']}%")
        print(f"Количество групп: {analytics['groups_count']}")
        
        print("\nАналитика по группам:")
        for group_data in analytics['by_groups']:
            print(f"  Группа {group_data['group_id']}:")
            print(f"    Просмотры: {group_data['views']}")
            print(f"    Клики: {group_data['clicks']}")
            print(f"    Репосты: {group_data['shares']}")
            print(f"    Реакции: {group_data['reactions']}")
            print(f"    CTR: {group_data['ctr']}%")
            print(f"    Вовлеченность: {group_data['engagement']}%")


async def get_analytics_summary_example():
    """Пример получения сводной аналитики за период"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Аналитика за последние 7 дней
        date_to = datetime.now()
        date_from = date_to - timedelta(days=7)
        
        summary = await uow.post_analytics_service.get_analytics_summary(date_from, date_to)
        
        print(f"\n=== Сводная аналитика за период ===")
        print(f"Период: {summary['period']['from']} - {summary['period']['to']}")
        print(f"Количество постов: {summary['posts_count']}")
        print(f"Всего просмотров: {summary['total_views']}")
        print(f"Всего кликов: {summary['total_clicks']}")
        print(f"Всего репостов: {summary['total_shares']}")
        print(f"Реакции: {summary['total_reactions']}")
        print(f"Средний CTR: {summary['average_ctr']}%")
        print(f"Средняя вовлеченность: {summary['average_engagement']}%")
        
        print("\nТоп-10 постов по просмотрам:")
        for i, post in enumerate(summary['top_posts'], 1):
            print(f"  {i}. Пост {post['post_id']} - {post['title'][:50]}...")
            print(f"     Просмотры: {post['views']}, CTR: {post['ctr']}%")


async def get_group_analytics_example():
    """Пример получения аналитики по группе"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        group_id = -1001234567890
        days = 30
        
        analytics = await uow.post_analytics_service.get_group_analytics(group_id, days)
        
        print(f"\n=== Аналитика группы {group_id} за {days} дней ===")
        print(f"Количество постов: {analytics['posts_count']}")
        print(f"Всего просмотров: {analytics['total_views']}")
        print(f"Всего кликов: {analytics['total_clicks']}")
        print(f"Всего репостов: {analytics['total_shares']}")
        print(f"Реакции: {analytics['total_reactions']}")
        print(f"Средний CTR: {analytics['average_ctr']}%")
        print(f"Средняя вовлеченность: {analytics['average_engagement']}%")


async def get_popular_reactions_example():
    """Пример получения популярных реакций"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        reactions = await uow.post_analytics_service.get_popular_reactions(days=30)
        
        print(f"\n=== Популярные реакции за 30 дней ===")
        for reaction, count in reactions.items():
            print(f"  {reaction}: {count}")


async def create_test_post_with_analytics():
    """Создание тестового поста с аналитикой"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Создаем тестовый пост
        post_data = {
            "title": "Тестовый пост для аналитики",
            "content": "Это тестовый пост для демонстрации аналитики",
            "status": PostStatus.PUBLISHED,
            "published_at": datetime.now()
        }
        
        post = await uow.admin_post_service.create_post(post_data)
        print(f"Создан тестовый пост с ID: {post.id}")
        
        # Симулируем активность
        group_ids = [-1001234567890, -1001234567891, -1001234567892]
        
        for group_id in group_ids:
            # Просмотры
            for _ in range(100 + group_id % 50):  # Разное количество просмотров
                await uow.post_analytics_service.track_view(post.id, group_id)
            
            # Клики
            for _ in range(10 + group_id % 10):
                await uow.post_analytics_service.track_click(post.id, group_id)
            
            # Репосты
            for _ in range(2 + group_id % 3):
                await uow.post_analytics_service.track_share(post.id, group_id)
            
            # Реакции
            reactions = ["👍", "❤️", "😂", "😮", "😢", "😡"]
            for reaction in reactions:
                for _ in range(group_id % 5 + 1):
                    await uow.post_analytics_service.track_reaction(post.id, group_id, reaction)
        
        await uow.commit()
        print(f"Аналитика для поста {post.id} создана")
        
        return post.id


async def telegram_bot_integration_example():
    """Пример интеграции с Telegram ботом"""
    print("\n=== Пример интеграции с Telegram ботом ===")
    print("""
# В обработчике сообщений бота
from aiogram import types
from database import get_session
from database.unit_of_work import UnitOfWork

@dp.message_handler(commands=['post_stats'])
async def post_stats_handler(message: types.Message):
    # Получаем ID поста из команды
    try:
        post_id = int(message.get_args())
    except (ValueError, TypeError):
        await message.reply("Укажите ID поста: /post_stats 123")
        return
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Получаем аналитику
        analytics = await uow.post_analytics_service.get_post_analytics(post_id)
        
        if not analytics or analytics['total_views'] == 0:
            await message.reply(f"Аналитика для поста {post_id} не найдена")
            return
        
        # Формируем ответ
        text = f"📊 Аналитика поста {post_id}:\n\n"
        text += f"👀 Просмотры: {analytics['total_views']}\n"
        text += f"👆 Клики: {analytics['total_clicks']}\n"
        text += f"📤 Репосты: {analytics['total_shares']}\n"
        text += f"📈 CTR: {analytics['average_ctr']}%\n"
        text += f"💫 Вовлеченность: {analytics['average_engagement']}%\n"
        text += f"📱 Групп: {analytics['groups_count']}"
        
        await message.reply(text)

# Отслеживание взаимодействий
@dp.callback_query_handler(lambda c: c.data.startswith('post_'))
async def post_interaction_handler(callback_query: types.CallbackQuery):
    post_id = int(callback_query.data.split('_')[1])
    group_id = callback_query.message.chat.id
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Отслеживаем клик
        await uow.post_analytics_service.track_click(post_id, group_id)
        await uow.commit()
    
    await callback_query.answer("Клик отслежен!")
    """)


async def main():
    """Главная функция с примерами"""
    print("=== Примеры использования PostAnalyticsService ===")
    
    # Создаем тестовый пост с аналитикой
    post_id = await create_test_post_with_analytics()
    
    # Отслеживаем дополнительные взаимодействия
    await track_post_interactions()
    
    # Получаем аналитику по посту
    await get_post_analytics_example()
    
    # Получаем сводную аналитику
    await get_analytics_summary_example()
    
    # Получаем аналитику по группе
    await get_group_analytics_example()
    
    # Получаем популярные реакции
    await get_popular_reactions_example()
    
    # Пример интеграции с ботом
    await telegram_bot_integration_example()


if __name__ == "__main__":
    asyncio.run(main())