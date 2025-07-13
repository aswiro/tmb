# examples/scheduler_usage.py

"""
Пример использования SchedulerService и PostScheduler
"""

import asyncio
from datetime import datetime, timedelta

from ..database import get_session
from ..database.unit_of_work import UnitOfWork
from ..database.models import PostStatus
from ..utilities.post_scheduler import init_post_scheduler, get_post_scheduler


async def example_create_and_schedule_post():
    """Пример создания и планирования поста"""
    print("=== Создание и планирование поста ===")
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Создаем черновик поста
        draft = await uow.admin_post_service.create_draft(
            user_id=1,
            content="Тестовый пост для планирования",
            media_urls=["https://example.com/image.jpg"]
        )
        
        print(f"Создан черновик поста ID: {draft.id}")
        
        # Планируем публикацию через 5 минут
        scheduled_time = datetime.now() + timedelta(minutes=5)
        
        scheduled_post = await uow.admin_post_service.schedule_post(
            draft.id,
            scheduled_time,
            target_groups=["@test_channel"]
        )
        
        print(f"Пост запланирован на: {scheduled_time}")
        
        # Добавляем в планировщик APScheduler
        scheduler = await get_post_scheduler()
        await scheduler.schedule_post(scheduled_post.id, scheduled_time)
        
        await uow.commit()
        
        return scheduled_post.id


async def example_reschedule_post(post_id: int):
    """Пример перепланирования поста"""
    print(f"=== Перепланирование поста {post_id} ===")
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Новое время - через 10 минут
        new_time = datetime.now() + timedelta(minutes=10)
        
        # Перепланируем в базе данных
        updated_post = await uow.scheduler_service.reschedule_post(post_id, new_time)
        
        if updated_post:
            print(f"Пост перепланирован на: {new_time}")
            
            # Обновляем в планировщике
            scheduler = await get_post_scheduler()
            await scheduler.reschedule_post(post_id, new_time)
            
            await uow.commit()
        else:
            print("Ошибка перепланирования поста")


async def example_cancel_post(post_id: int):
    """Пример отмены запланированного поста"""
    print(f"=== Отмена поста {post_id} ===")
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Отменяем в базе данных
        cancelled_post = await uow.admin_post_service.cancel_post(
            post_id, 
            "Отменено пользователем"
        )
        
        if cancelled_post:
            print("Пост отменен в базе данных")
            
            # Отменяем в планировщике
            scheduler = await get_post_scheduler()
            await scheduler.cancel_scheduled_post(post_id)
            
            await uow.commit()
        else:
            print("Ошибка отмены поста")


async def example_get_scheduler_stats():
    """Пример получения статистики планировщика"""
    print("=== Статистика планировщика ===")
    
    # Статистика из базы данных
    async with get_session() as session:
        uow = UnitOfWork(session)
        db_stats = await uow.scheduler_service.get_scheduler_stats()
        
        print("Статистика из БД:")
        print(f"  Запланировано: {db_stats['scheduled_count']}")
        print(f"  Опубликовано: {db_stats['published_count']}")
        print(f"  Ошибок: {db_stats['error_count']}")
        print(f"  Готово к публикации: {db_stats['ready_to_publish']}")
    
    # Статистика планировщика
    scheduler = await get_post_scheduler()
    scheduler_stats = await scheduler.get_scheduler_status()
    
    print("\nСтатистика планировщика:")
    print(f"  Запущен: {scheduler_stats['running']}")
    print(f"  Активных заданий: {scheduler_stats['scheduled_jobs']}")


async def example_get_scheduled_posts():
    """Пример получения списка запланированных постов"""
    print("=== Запланированные посты ===")
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Получаем следующие 5 постов
        next_posts = await uow.scheduler_service.get_next_scheduled_posts(limit=5)
        
        if next_posts:
            print(f"Найдено {len(next_posts)} запланированных постов:")
            for post in next_posts:
                print(f"  ID: {post.id}, время: {post.scheduled_at}, статус: {post.status}")
        else:
            print("Запланированных постов не найдено")
    
    # Получаем задания из планировщика
    scheduler = await get_post_scheduler()
    scheduled_jobs = scheduler.get_scheduled_jobs()
    
    if scheduled_jobs:
        print(f"\nАктивных заданий в планировщике: {len(scheduled_jobs)}")
        for job in scheduled_jobs:
            print(f"  Job ID: {job['id']}, следующий запуск: {job['next_run_time']}")
    else:
        print("\nАктивных заданий в планировщике нет")


async def example_create_poll_post():
    """Пример создания поста с опросом"""
    print("=== Создание поста с опросом ===")
    
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Создаем пост с опросом
        poll_post = await uow.admin_post_service.create_poll_post(
            user_id=1,
            question="Какой язык программирования вам нравится больше?",
            options=["Python", "JavaScript", "Go", "Rust"],
            allows_multiple_answers=False,
            is_anonymous=True
        )
        
        print(f"Создан пост с опросом ID: {poll_post.id}")
        print(f"Вопрос: {poll_post.poll.question}")
        print("Варианты ответов:")
        for option in poll_post.poll.options:
            print(f"  - {option.text}")
        
        await uow.commit()
        
        return poll_post.id


async def main():
    """Основная функция с примерами использования"""
    print("Запуск примеров использования SchedulerService\n")
    
    try:
        # Инициализируем планировщик
        await init_post_scheduler()
        print("Планировщик инициализирован\n")
        
        # Создаем и планируем пост
        post_id = await example_create_and_schedule_post()
        print()
        
        # Получаем статистику
        await example_get_scheduler_stats()
        print()
        
        # Получаем список запланированных постов
        await example_get_scheduled_posts()
        print()
        
        # Создаем пост с опросом
        poll_post_id = await example_create_poll_post()
        print()
        
        # Перепланируем пост
        await example_reschedule_post(post_id)
        print()
        
        # Ждем немного
        print("Ожидание 5 секунд...")
        await asyncio.sleep(5)
        
        # Отменяем пост
        await example_cancel_post(post_id)
        print()
        
        # Финальная статистика
        await example_get_scheduler_stats()
        
    except Exception as e:
        print(f"Ошибка: {e}")
    
    finally:
        # Останавливаем планировщик
        from ..utilities.post_scheduler import shutdown_post_scheduler
        await shutdown_post_scheduler()
        print("\nПланировщик остановлен")


if __name__ == "__main__":
    asyncio.run(main())