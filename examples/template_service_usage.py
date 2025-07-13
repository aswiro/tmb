"""Примеры использования TemplateService для управления шаблонами постов"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from database.db_main import get_session
from database.unit_of_work import UnitOfWork
from database.models.admin_post import MediaType


async def create_template_example():
    """Пример создания шаблона поста"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Создание простого текстового шаблона
        template = await uow.template_service.create_template(
            title="Ежедневная сводка новостей",
            content="📰 Сводка новостей за {date}\n\n{news_content}\n\n#новости #сводка",
            template_name="daily_news",
            template_description="Шаблон для ежедневных новостных сводок",
            created_by=123456789,
            hashtags=["новости", "сводка", "ежедневно"],
            categories=["Новости", "Ежедневные"]
        )
        
        print(f"Создан шаблон: {template.template_name} (ID: {template.id})")
        
        # Создание шаблона с медиа
        media_template = await uow.template_service.create_template(
            title="Промо-пост с изображением",
            content="🎉 Специальное предложение!\n\n{offer_description}\n\n💰 Скидка: {discount}%\n⏰ До: {end_date}",
            template_name="promo_image",
            template_description="Шаблон для промо-постов с изображением",
            created_by=123456789,
            media_type=MediaType.PHOTO,
            media_caption="Специальное предложение",
            hashtags=["промо", "скидка", "предложение"],
            categories=["Промо", "Маркетинг"]
        )
        
        print(f"Создан медиа-шаблон: {media_template.template_name} (ID: {media_template.id})")
        
        await session.commit()
        return template, media_template


async def manage_templates_example():
    """Пример управления шаблонами"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        user_id = 123456789
        
        # Получение списка шаблонов пользователя
        templates = await uow.template_service.get_user_templates(
            user_id=user_id,
            limit=10,
            search="новости"
        )
        
        print(f"Найдено шаблонов: {len(templates)}")
        for template in templates:
            print(f"- {template.template_name}: {template.title}")
        
        if templates:
            template = templates[0]
            
            # Обновление шаблона
            updated_template = await uow.template_service.update_template(
                template_id=template.id,
                user_id=user_id,
                template_description="Обновленное описание шаблона",
                hashtags=["новости", "сводка", "обновлено"]
            )
            
            print(f"Обновлен шаблон: {updated_template.template_name}")
            
            # Дублирование шаблона
            duplicate = await uow.template_service.duplicate_template(
                template_id=template.id,
                user_id=user_id,
                new_template_name="daily_news_copy"
            )
            
            print(f"Создана копия: {duplicate.template_name}")
        
        await session.commit()


async def create_post_from_template_example():
    """Пример создания поста на основе шаблона"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        user_id = 123456789
        
        # Получаем шаблон
        template = await uow.template_service.get_template_by_name(
            template_name="daily_news",
            user_id=user_id
        )
        
        if template:
            # Создание поста на основе шаблона
            post = await uow.template_service.create_post_from_template(
                template_id=template.id,
                user_id=user_id,
                title="Новости за 15 декабря 2024",
                content=template.content.replace(
                    "{date}", "15 декабря 2024"
                ).replace(
                    "{news_content}", "Сегодня произошли важные события..."
                ),
                target_groups=[1001, 1002],
                scheduled_at=datetime.now() + timedelta(hours=1),
                additional_hashtags=["15декабря"],
                additional_categories=["Актуальное"]
            )
            
            print(f"Создан пост из шаблона: {post.title} (ID: {post.id})")
            print(f"Статус: {post.status}")
            print(f"Запланирован на: {post.scheduled_at}")
        
        await session.commit()


async def template_categories_and_stats_example():
    """Пример работы с категориями и статистикой шаблонов"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        user_id = 123456789
        
        # Получение категорий
        categories = await uow.template_service.get_template_categories(user_id)
        print(f"Категории шаблонов: {categories}")
        
        # Получение статистики
        stats = await uow.template_service.get_template_statistics(user_id)
        print("Статистика шаблонов:")
        print(f"- Всего шаблонов: {stats.get('total_templates', 0)}")
        print(f"- Категорий: {stats.get('categories_count', 0)}")
        print(f"- Распределение по категориям: {stats.get('category_distribution', {})}")
        print(f"- Распределение по типам медиа: {stats.get('media_type_distribution', {})}")
        
        # Получение шаблонов по категории
        if categories:
            category_templates = await uow.template_service.get_user_templates(
                user_id=user_id,
                category=categories[0],
                limit=5
            )
            print(f"Шаблоны в категории '{categories[0]}': {len(category_templates)}")


async def search_and_recommendations_example():
    """Пример поиска и рекомендаций шаблонов"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        user_id = 123456789
        
        # Поиск шаблонов
        search_results = await uow.template_service.search_templates(
            user_id=user_id,
            query="новости",
            limit=5,
            include_content=True
        )
        
        print(f"Результаты поиска по 'новости': {len(search_results)}")
        for template in search_results:
            print(f"- {template.template_name}: {template.title}")
        
        # Рекомендации на основе категорий
        recommendations = await uow.template_service.get_recommended_templates(
            user_id=user_id,
            based_on_categories=["Новости", "Промо"],
            limit=3
        )
        
        print(f"Рекомендованные шаблоны: {len(recommendations)}")
        for template in recommendations:
            print(f"- {template.template_name}: {template.categories}")


async def export_import_example():
    """Пример экспорта и импорта шаблонов"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        user_id = 123456789
        
        # Получаем шаблон для экспорта
        template = await uow.template_service.get_template_by_name(
            template_name="daily_news",
            user_id=user_id
        )
        
        if template:
            # Экспорт шаблона
            export_data = await uow.template_service.export_template(
                template_id=template.id,
                user_id=user_id
            )
            
            print("Экспортированные данные:")
            print(f"- Название: {export_data['template_name']}")
            print(f"- Версия: {export_data['version']}")
            print(f"- Дата экспорта: {export_data['exported_at']}")
            
            # Изменяем данные для импорта
            import_data = export_data.copy()
            import_data['template_name'] = 'imported_daily_news'
            import_data['title'] = 'Импортированный шаблон новостей'
            
            # Импорт шаблона
            imported_template = await uow.template_service.import_template(
                template_data=import_data,
                user_id=user_id
            )
            
            print(f"Импортирован шаблон: {imported_template.template_name} (ID: {imported_template.id})")
        
        await session.commit()


async def telegram_bot_integration_example():
    """Пример интеграции с Telegram ботом"""
    # Этот пример показывает, как можно использовать TemplateService в боте
    
    async def handle_create_template_command(message, user_id: int):
        """Обработчик команды создания шаблона"""
        async with get_session() as session:
            uow = UnitOfWork(session)
            
            try:
                # Парсим данные из сообщения
                lines = message.text.split('\n')
                template_name = lines[1].replace('Название: ', '')
                title = lines[2].replace('Заголовок: ', '')
                content = '\n'.join(lines[3:])
                
                template = await uow.template_service.create_template(
                    title=title,
                    content=content,
                    template_name=template_name,
                    created_by=user_id,
                    categories=["Пользовательские"]
                )
                
                await session.commit()
                return f"✅ Шаблон '{template_name}' создан успешно!"
                
            except Exception as e:
                await session.rollback()
                return f"❌ Ошибка создания шаблона: {str(e)}"
    
    async def handle_list_templates_command(user_id: int):
        """Обработчик команды списка шаблонов"""
        async with get_session() as session:
            uow = UnitOfWork(session)
            
            templates = await uow.template_service.get_user_templates(
                user_id=user_id,
                limit=10
            )
            
            if not templates:
                return "📝 У вас пока нет шаблонов"
            
            response = "📋 Ваши шаблоны:\n\n"
            for i, template in enumerate(templates, 1):
                response += f"{i}. {template.template_name}\n"
                response += f"   📄 {template.title}\n"
                if template.categories:
                    response += f"   🏷 {', '.join(template.categories)}\n"
                response += "\n"
            
            return response
    
    async def handle_use_template_command(template_name: str, user_id: int, target_groups: List[int]):
        """Обработчик команды использования шаблона"""
        async with get_session() as session:
            uow = UnitOfWork(session)
            
            try:
                template = await uow.template_service.get_template_by_name(
                    template_name=template_name,
                    user_id=user_id
                )
                
                if not template:
                    return f"❌ Шаблон '{template_name}' не найден"
                
                post = await uow.template_service.create_post_from_template(
                    template_id=template.id,
                    user_id=user_id,
                    target_groups=target_groups,
                    scheduled_at=datetime.now() + timedelta(minutes=5)
                )
                
                await session.commit()
                return f"✅ Пост создан на основе шаблона '{template_name}' и запланирован на публикацию"
                
            except Exception as e:
                await session.rollback()
                return f"❌ Ошибка создания поста: {str(e)}"
    
    # Примеры использования в боте
    print("Примеры команд для Telegram бота:")
    print("/create_template - создать новый шаблон")
    print("/list_templates - показать список шаблонов")
    print("/use_template <название> - использовать шаблон")
    print("/template_stats - показать статистику шаблонов")


async def advanced_template_management_example():
    """Пример продвинутого управления шаблонами"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        user_id = 123456789
        
        # Создание набора шаблонов для разных целей
        templates_data = [
            {
                "title": "Утренняя мотивация",
                "content": "🌅 Доброе утро!\n\n{motivation_text}\n\n#мотивация #утро #позитив",
                "template_name": "morning_motivation",
                "template_description": "Шаблон для утренних мотивационных постов",
                "categories": ["Мотивация", "Утро"]
            },
            {
                "title": "Вечерние размышления",
                "content": "🌙 Вечерние мысли...\n\n{thoughts}\n\n#размышления #вечер #философия",
                "template_name": "evening_thoughts",
                "template_description": "Шаблон для вечерних философских постов",
                "categories": ["Философия", "Вечер"]
            },
            {
                "title": "Обзор продукта",
                "content": "📦 Обзор: {product_name}\n\n✅ Плюсы:\n{pros}\n\n❌ Минусы:\n{cons}\n\n⭐ Оценка: {rating}/10",
                "template_name": "product_review",
                "template_description": "Шаблон для обзоров продуктов",
                "categories": ["Обзоры", "Продукты"]
            }
        ]
        
        created_templates = []
        for template_data in templates_data:
            try:
                template = await uow.template_service.create_template(
                    created_by=user_id,
                    **template_data
                )
                created_templates.append(template)
                print(f"Создан шаблон: {template.template_name}")
            except Exception as e:
                print(f"Ошибка создания шаблона {template_data['template_name']}: {e}")
        
        # Массовое создание постов из шаблонов
        posts_data = [
            {
                "template_name": "morning_motivation",
                "content_replacements": {
                    "{motivation_text}": "Каждый новый день - это возможность стать лучше!"
                },
                "target_groups": [1001]
            },
            {
                "template_name": "product_review",
                "content_replacements": {
                    "{product_name}": "iPhone 15 Pro",
                    "{pros}": "- Отличная камера\n- Быстрая работа\n- Премиум дизайн",
                    "{cons}": "- Высокая цена\n- Быстро разряжается",
                    "{rating}": "8"
                },
                "target_groups": [1002, 1003]
            }
        ]
        
        for post_data in posts_data:
            try:
                template = await uow.template_service.get_template_by_name(
                    template_name=post_data["template_name"],
                    user_id=user_id
                )
                
                if template:
                    # Заменяем плейсхолдеры в контенте
                    content = template.content
                    for placeholder, replacement in post_data["content_replacements"].items():
                        content = content.replace(placeholder, replacement)
                    
                    post = await uow.template_service.create_post_from_template(
                        template_id=template.id,
                        user_id=user_id,
                        content=content,
                        target_groups=post_data["target_groups"],
                        scheduled_at=datetime.now() + timedelta(minutes=10)
                    )
                    
                    print(f"Создан пост из шаблона '{post_data['template_name']}': {post.id}")
            
            except Exception as e:
                print(f"Ошибка создания поста из шаблона {post_data['template_name']}: {e}")
        
        await session.commit()
        
        # Финальная статистика
        stats = await uow.template_service.get_template_statistics(user_id)
        print(f"\nИтоговая статистика: {stats['total_templates']} шаблонов в {stats['categories_count']} категориях")


async def main():
    """Главная функция с примерами использования"""
    print("=== Примеры использования TemplateService ===")
    
    try:
        print("\n1. Создание шаблонов")
        await create_template_example()
        
        print("\n2. Управление шаблонами")
        await manage_templates_example()
        
        print("\n3. Создание постов из шаблонов")
        await create_post_from_template_example()
        
        print("\n4. Категории и статистика")
        await template_categories_and_stats_example()
        
        print("\n5. Поиск и рекомендации")
        await search_and_recommendations_example()
        
        print("\n6. Экспорт и импорт")
        await export_import_example()
        
        print("\n7. Интеграция с Telegram ботом")
        await telegram_bot_integration_example()
        
        print("\n8. Продвинутое управление")
        await advanced_template_management_example()
        
    except Exception as e:
        print(f"Ошибка выполнения примеров: {e}")


if __name__ == "__main__":
    asyncio.run(main())