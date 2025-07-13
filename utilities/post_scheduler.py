# utilities/post_scheduler.py

import asyncio
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from loguru import logger

from ..database import get_session
from ..database.unit_of_work import UnitOfWork


class PostScheduler:
    """Планировщик постов с использованием APScheduler"""

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        # Настройка хранилища заданий в Redis
        jobstores = {
            'default': RedisJobStore(
                host='localhost',
                port=6379,
                db=1,
                password=None
            )
        }
        
        # Настройка исполнителей
        executors = {
            'default': AsyncIOExecutor()
        }
        
        # Настройки планировщика
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        self._running = False

    async def start(self):
        """Запуск планировщика"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            
            # Добавляем периодическую задачу проверки постов
            self.scheduler.add_job(
                self._check_scheduled_posts,
                'interval',
                minutes=1,  # Проверяем каждую минуту
                id='check_scheduled_posts',
                replace_existing=True
            )
            
            # Добавляем задачу очистки истекших постов
            self.scheduler.add_job(
                self._expire_posts,
                'interval',
                hours=1,  # Проверяем каждый час
                id='expire_posts',
                replace_existing=True
            )
            
            logger.info("Post scheduler started")

    async def stop(self):
        """Остановка планировщика"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("Post scheduler stopped")

    async def schedule_post(self, post_id: int, scheduled_at: datetime) -> bool:
        """Планирование публикации поста"""
        try:
            job_id = f"publish_post_{post_id}"
            
            # Удаляем существующее задание если есть
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Добавляем новое задание
            self.scheduler.add_job(
                self._publish_post,
                'date',
                run_date=scheduled_at,
                args=[post_id],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"Scheduled post {post_id} for {scheduled_at}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling post {post_id}: {e}")
            return False

    async def cancel_scheduled_post(self, post_id: int) -> bool:
        """Отмена запланированной публикации поста"""
        try:
            job_id = f"publish_post_{post_id}"
            
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Cancelled scheduled post {post_id}")
                return True
            else:
                logger.warning(f"No scheduled job found for post {post_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling scheduled post {post_id}: {e}")
            return False

    async def reschedule_post(self, post_id: int, new_scheduled_at: datetime) -> bool:
        """Перепланирование поста"""
        try:
            # Отменяем старое задание
            await self.cancel_scheduled_post(post_id)
            
            # Создаем новое
            return await self.schedule_post(post_id, new_scheduled_at)
            
        except Exception as e:
            logger.error(f"Error rescheduling post {post_id}: {e}")
            return False

    async def _check_scheduled_posts(self):
        """Периодическая проверка запланированных постов"""
        try:
            async with get_session() as session:
                uow = UnitOfWork(session)
                await uow.scheduler_service.check_scheduled_posts()
                await uow.commit()
                
        except Exception as e:
            logger.error(f"Error in scheduled posts check: {e}")

    async def _expire_posts(self):
        """Периодическая очистка истекших постов"""
        try:
            async with get_session() as session:
                uow = UnitOfWork(session)
                await uow.scheduler_service.expire_posts()
                await uow.commit()
                
        except Exception as e:
            logger.error(f"Error in posts expiration: {e}")

    async def _publish_post(self, post_id: int):
        """Публикация конкретного поста"""
        try:
            async with get_session() as session:
                uow = UnitOfWork(session)
                
                # Получаем пост
                post = await uow.admin_posts.get_by_id(post_id)
                if not post:
                    logger.error(f"Post {post_id} not found")
                    return
                
                # Публикуем через сервис
                success = await uow.scheduler_service.publish_scheduled_post(post)
                
                if success:
                    await uow.commit()
                    logger.info(f"Successfully published post {post_id}")
                else:
                    await uow.rollback()
                    logger.error(f"Failed to publish post {post_id}")
                    
        except Exception as e:
            logger.error(f"Error publishing post {post_id}: {e}")

    def get_scheduled_jobs(self) -> list:
        """Получение списка запланированных заданий"""
        return [
            {
                'id': job.id,
                'next_run_time': job.next_run_time,
                'args': job.args
            }
            for job in self.scheduler.get_jobs()
            if job.id.startswith('publish_post_')
        ]

    async def get_scheduler_status(self) -> dict:
        """Получение статуса планировщика"""
        try:
            async with get_session() as session:
                uow = UnitOfWork(session)
                stats = await uow.scheduler_service.get_scheduler_stats()
                
                return {
                    'running': self._running,
                    'scheduled_jobs': len(self.get_scheduled_jobs()),
                    **stats
                }
                
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                'running': self._running,
                'scheduled_jobs': 0,
                'error': str(e)
            }


# Глобальный экземпляр планировщика
post_scheduler: Optional[PostScheduler] = None


async def init_post_scheduler(redis_url: str = "redis://localhost:6379/1") -> PostScheduler:
    """Инициализация глобального планировщика постов"""
    global post_scheduler
    
    if post_scheduler is None:
        post_scheduler = PostScheduler(redis_url)
        await post_scheduler.start()
    
    return post_scheduler


async def get_post_scheduler() -> PostScheduler:
    """Получение экземпляра планировщика постов"""
    global post_scheduler
    
    if post_scheduler is None:
        raise RuntimeError("Post scheduler not initialized. Call init_post_scheduler() first.")
    
    return post_scheduler


async def shutdown_post_scheduler():
    """Остановка планировщика постов"""
    global post_scheduler
    
    if post_scheduler is not None:
        await post_scheduler.stop()
        post_scheduler = None