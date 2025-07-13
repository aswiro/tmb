from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.models.admin_post import AdminPost, MediaType, PostStatus
from database.repository import Repository


class TemplateService:
    """Сервис для управления шаблонами постов"""

    def __init__(self, session: AsyncSession, repository: Repository):
        self.session = session
        self.repository = repository

    # Создание и управление шаблонами
    async def create_template(
        self,
        title: str,
        content: str,
        template_name: str,
        created_by: int,
        template_description: str | None = None,
        media_type: MediaType | None = None,
        media_file_id: str | None = None,
        media_caption: str | None = None,
        hashtags: list[str] | None = None,
        links: list[dict[str, str]] | None = None,
        categories: list[str] | None = None,
    ) -> AdminPost:
        """Создание нового шаблона поста"""
        try:
            # Проверяем уникальность имени шаблона для пользователя
            existing_template = await self._get_template_by_name(
                template_name, created_by
            )
            if existing_template:
                raise ValueError(f"Шаблон с именем '{template_name}' уже существует")

            template_data = {
                "title": title,
                "content": content,
                "template_name": template_name,
                "template_description": template_description,
                "is_template": True,
                "status": PostStatus.DRAFT,
                "created_by": created_by,
                "media_type": media_type,
                "media_file_id": media_file_id,
                "media_caption": media_caption,
                "hashtags": hashtags or [],
                "links": links or [],
                "categories": categories or [],
            }

            template = await self.repository.admin_post.create(**template_data)
            logger.info(
                f"Создан шаблон '{template_name}' (ID: {template.id}) пользователем {created_by}"
            )
            return template

        except Exception as e:
            logger.error(f"Ошибка создания шаблона: {e}")
            raise

    async def update_template(  # noqa: C901
        self,
        template_id: int,
        user_id: int,
        title: str | None = None,
        content: str | None = None,
        template_name: str | None = None,
        template_description: str | None = None,
        media_type: MediaType | None = None,
        media_file_id: str | None = None,
        media_caption: str | None = None,
        hashtags: list[str] | None = None,
        links: list[dict[str, str]] | None = None,
        categories: list[str] | None = None,
    ) -> AdminPost:
        """Обновление существующего шаблона"""
        try:
            template = await self._get_template_by_id(template_id, user_id)
            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            # Проверяем уникальность нового имени шаблона
            if template_name and template_name != template.template_name:
                existing_template = await self._get_template_by_name(
                    template_name, user_id
                )
                if existing_template and existing_template.id != template_id:
                    raise ValueError(
                        f"Шаблон с именем '{template_name}' уже существует"
                    )

            update_data = {}
            if title is not None:
                update_data["title"] = title
            if content is not None:
                update_data["content"] = content
            if template_name is not None:
                update_data["template_name"] = template_name
            if template_description is not None:
                update_data["template_description"] = template_description
            if media_type is not None:
                update_data["media_type"] = media_type
            if media_file_id is not None:
                update_data["media_file_id"] = media_file_id
            if media_caption is not None:
                update_data["media_caption"] = media_caption
            if hashtags is not None:
                update_data["hashtags"] = hashtags
            if links is not None:
                update_data["links"] = links
            if categories is not None:
                update_data["categories"] = categories

            if update_data:
                updated_template = await self.repository.admin_post.update(
                    template_id, **update_data
                )
                logger.info(
                    f"Обновлен шаблон '{template.template_name}' (ID: {template_id})"
                )
                return updated_template

            return template

        except Exception as e:
            logger.error(f"Ошибка обновления шаблона: {e}")
            raise

    async def delete_template(self, template_id: int, user_id: int) -> bool:
        """Удаление шаблона"""
        try:
            template = await self._get_template_by_id(template_id, user_id)
            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            await self.repository.admin_post.delete(template_id)
            logger.info(f"Удален шаблон '{template.template_name}' (ID: {template_id})")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления шаблона: {e}")
            raise

    # Получение шаблонов
    async def get_template_by_id(
        self, template_id: int, user_id: int
    ) -> AdminPost | None:
        """Получение шаблона по ID"""
        return await self._get_template_by_id(template_id, user_id)

    async def get_template_by_name(
        self, template_name: str, user_id: int
    ) -> AdminPost | None:
        """Получение шаблона по имени"""
        return await self._get_template_by_name(template_name, user_id)

    async def get_user_templates(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        category: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[AdminPost]:
        """Получение списка шаблонов пользователя"""
        try:
            query = select(AdminPost).where(
                and_(AdminPost.created_by == user_id, AdminPost.is_template)
            )

            # Поиск по названию или описанию
            if search:
                search_filter = or_(
                    AdminPost.template_name.ilike(f"%{search}%"),
                    AdminPost.template_description.ilike(f"%{search}%"),
                    AdminPost.title.ilike(f"%{search}%"),
                    AdminPost.content.ilike(f"%{search}%"),
                )
                query = query.where(search_filter)

            # Фильтр по категории
            if category:
                query = query.where(AdminPost.categories.contains([category]))

            # Сортировка
            if sort_order == "desc":
                query = query.order_by(desc(getattr(AdminPost, sort_by)))
            else:
                query = query.order_by(asc(getattr(AdminPost, sort_by)))

            # Пагинация
            query = query.offset(offset).limit(limit)

            result = await self.session.execute(query)
            templates = result.scalars().all()

            logger.info(
                f"Получено {len(templates)} шаблонов для пользователя {user_id}"
            )
            return list(templates)

        except Exception as e:
            logger.error(f"Ошибка получения шаблонов: {e}")
            raise

    async def get_templates_count(
        self,
        user_id: int,
        search: str | None = None,
        category: str | None = None,
    ) -> int:
        """Получение количества шаблонов пользователя"""
        try:
            query = select(AdminPost).where(
                and_(AdminPost.created_by == user_id, AdminPost.is_template)
            )

            if search:
                search_filter = or_(
                    AdminPost.template_name.ilike(f"%{search}%"),
                    AdminPost.template_description.ilike(f"%{search}%"),
                    AdminPost.title.ilike(f"%{search}%"),
                    AdminPost.content.ilike(f"%{search}%"),
                )
                query = query.where(search_filter)

            if category:
                query = query.where(AdminPost.categories.contains([category]))

            result = await self.session.execute(query)
            return len(result.scalars().all())

        except Exception as e:
            logger.error(f"Ошибка подсчета шаблонов: {e}")
            return 0

    # Использование шаблонов
    async def create_post_from_template(
        self,
        template_id: int,
        user_id: int,
        title: str | None = None,
        content: str | None = None,
        target_groups: list[int] | None = None,
        scheduled_at: datetime | None = None,
        expires_at: datetime | None = None,
        priority: int = 0,
        override_media: bool = False,
        new_media_type: MediaType | None = None,
        new_media_file_id: str | None = None,
        new_media_caption: str | None = None,
        additional_hashtags: list[str] | None = None,
        additional_links: list[dict[str, str]] | None = None,
        additional_categories: list[str] | None = None,
    ) -> AdminPost:
        """Создание поста на основе шаблона"""
        try:
            template = await self._get_template_by_id(template_id, user_id)
            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            # Подготавливаем данные для нового поста
            post_data = {
                "title": title or template.title,
                "content": content or template.content,
                "is_template": False,
                "template_name": None,
                "template_description": None,
                "created_by": user_id,
                "target_groups": target_groups or [],
                "scheduled_at": scheduled_at,
                "expires_at": expires_at,
                "priority": priority,
                "status": PostStatus.SCHEDULED if scheduled_at else PostStatus.DRAFT,
            }

            # Медиа контент
            if override_media:
                post_data.update(
                    {
                        "media_type": new_media_type,
                        "media_file_id": new_media_file_id,
                        "media_caption": new_media_caption,
                    }
                )
            else:
                post_data.update(
                    {
                        "media_type": template.media_type,
                        "media_file_id": template.media_file_id,
                        "media_caption": template.media_caption,
                    }
                )

            # Хештеги
            hashtags = list(template.hashtags or [])
            if additional_hashtags:
                hashtags.extend(additional_hashtags)
            post_data["hashtags"] = list(set(hashtags))  # Убираем дубликаты

            # Ссылки
            links = list(template.links or [])
            if additional_links:
                links.extend(additional_links)
            post_data["links"] = links

            # Категории
            categories = list(template.categories or [])
            if additional_categories:
                categories.extend(additional_categories)
            post_data["categories"] = list(set(categories))  # Убираем дубликаты

            new_post = await self.repository.admin_post.create(**post_data)
            logger.info(
                f"Создан пост (ID: {new_post.id}) на основе шаблона '{template.template_name}'"
            )
            return new_post

        except Exception as e:
            logger.error(f"Ошибка создания поста из шаблона: {e}")
            raise

    async def duplicate_template(
        self, template_id: int, user_id: int, new_template_name: str
    ) -> AdminPost:
        """Дублирование шаблона"""
        try:
            template = await self._get_template_by_id(template_id, user_id)
            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            # Проверяем уникальность нового имени
            existing_template = await self._get_template_by_name(
                new_template_name, user_id
            )
            if existing_template:
                raise ValueError(
                    f"Шаблон с именем '{new_template_name}' уже существует"
                )

            duplicate_data = {
                "title": f"Копия: {template.title}",
                "content": template.content,
                "template_name": new_template_name,
                "template_description": template.template_description,
                "is_template": True,
                "status": PostStatus.DRAFT,
                "created_by": user_id,
                "media_type": template.media_type,
                "media_file_id": template.media_file_id,
                "media_caption": template.media_caption,
                "hashtags": template.hashtags,
                "links": template.links,
                "categories": template.categories,
            }

            duplicate = await self.repository.admin_post.create(**duplicate_data)
            logger.info(
                f"Создана копия шаблона '{template.template_name}' -> '{new_template_name}'"
            )
            return duplicate

        except Exception as e:
            logger.error(f"Ошибка дублирования шаблона: {e}")
            raise

    # Категории и статистика
    async def get_template_categories(self, user_id: int) -> list[str]:
        """Получение списка категорий шаблонов пользователя"""
        try:
            query = select(AdminPost.categories).where(
                and_(AdminPost.created_by == user_id, AdminPost.is_template)
            )
            result = await self.session.execute(query)
            all_categories = result.scalars().all()

            # Собираем уникальные категории
            categories = set()
            for category_list in all_categories:
                if category_list:
                    categories.update(category_list)

            return sorted(categories)

        except Exception as e:
            logger.error(f"Ошибка получения категорий шаблонов: {e}")
            return []

    async def get_template_statistics(self, user_id: int) -> dict[str, Any]:
        """Получение статистики по шаблонам пользователя"""
        try:
            templates = await self.get_user_templates(user_id, limit=1000)
            categories = await self.get_template_categories(user_id)

            # Подсчет по категориям
            category_stats = {}
            for category in categories:
                count = len(
                    [t for t in templates if t.categories and category in t.categories]
                )
                category_stats[category] = count

            # Подсчет по типам медиа
            media_stats = {}
            for template in templates:
                media_type = (
                    template.media_type.value if template.media_type else "text"
                )
                media_stats[media_type] = media_stats.get(media_type, 0) + 1

            return {
                "total_templates": len(templates),
                "categories_count": len(categories),
                "category_distribution": category_stats,
                "media_type_distribution": media_stats,
                "most_recent": (
                    templates[0].created_at.isoformat() if templates else None
                ),
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики шаблонов: {e}")
            return {}

    # Приватные методы
    async def _get_template_by_id(
        self, template_id: int, user_id: int
    ) -> AdminPost | None:
        """Получение шаблона по ID с проверкой владельца"""
        query = select(AdminPost).where(
            and_(
                AdminPost.id == template_id,
                AdminPost.created_by == user_id,
                AdminPost.is_template,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_template_by_name(
        self, template_name: str, user_id: int
    ) -> AdminPost | None:
        """Получение шаблона по имени с проверкой владельца"""
        query = select(AdminPost).where(
            and_(
                AdminPost.template_name == template_name,
                AdminPost.created_by == user_id,
                AdminPost.is_template,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # Экспорт и импорт шаблонов
    async def export_template(self, template_id: int, user_id: int) -> dict[str, Any]:
        """Экспорт шаблона в JSON формат"""
        try:
            template = await self._get_template_by_id(template_id, user_id)
            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            export_data = {
                "template_name": template.template_name,
                "template_description": template.template_description,
                "title": template.title,
                "content": template.content,
                "media_type": template.media_type.value
                if template.media_type
                else None,
                "media_caption": template.media_caption,
                "hashtags": template.hashtags,
                "links": template.links,
                "categories": template.categories,
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
            }

            logger.info(f"Экспортирован шаблон '{template.template_name}'")
            return export_data

        except Exception as e:
            logger.error(f"Ошибка экспорта шаблона: {e}")
            raise

    async def import_template(
        self, template_data: dict[str, Any], user_id: int
    ) -> AdminPost:
        """Импорт шаблона из JSON формата"""
        try:
            required_fields = ["template_name", "title", "content"]
            for field in required_fields:
                if field not in template_data:
                    raise ValueError(f"Отсутствует обязательное поле: {field}")

            # Проверяем уникальность имени
            existing_template = await self._get_template_by_name(
                template_data["template_name"], user_id
            )
            if existing_template:
                # Добавляем суффикс к имени
                base_name = template_data["template_name"]
                counter = 1
                while existing_template:
                    new_name = f"{base_name} ({counter})"
                    existing_template = await self._get_template_by_name(
                        new_name, user_id
                    )
                    counter += 1
                template_data["template_name"] = new_name

            # Преобразуем media_type обратно в enum
            media_type = None
            if template_data.get("media_type"):
                try:
                    media_type = MediaType(template_data["media_type"])
                except ValueError:
                    logger.warning(
                        f"Неизвестный тип медиа: {template_data['media_type']}"
                    )

            import_data = {
                "title": template_data["title"],
                "content": template_data["content"],
                "template_name": template_data["template_name"],
                "template_description": template_data.get("template_description"),
                "is_template": True,
                "status": PostStatus.DRAFT,
                "created_by": user_id,
                "media_type": media_type,
                "media_caption": template_data.get("media_caption"),
                "hashtags": template_data.get("hashtags", []),
                "links": template_data.get("links", []),
                "categories": template_data.get("categories", []),
            }

            template = await self.repository.admin_post.create(**import_data)
            logger.info(
                f"Импортирован шаблон '{template.template_name}' (ID: {template.id})"
            )
            return template

        except Exception as e:
            logger.error(f"Ошибка импорта шаблона: {e}")
            raise

    # Поиск и рекомендации
    async def search_templates(
        self,
        user_id: int,
        query: str,
        limit: int = 20,
        include_content: bool = True,
    ) -> list[AdminPost]:
        """Расширенный поиск по шаблонам"""
        try:
            search_query = select(AdminPost).where(
                and_(AdminPost.created_by == user_id, AdminPost.is_template)
            )

            # Поиск по различным полям
            search_conditions = [
                AdminPost.template_name.ilike(f"%{query}%"),
                AdminPost.template_description.ilike(f"%{query}%"),
                AdminPost.title.ilike(f"%{query}%"),
            ]

            if include_content:
                search_conditions.append(AdminPost.content.ilike(f"%{query}%"))

            # Поиск по хештегам и категориям
            search_conditions.extend(
                [
                    AdminPost.hashtags.contains([query]),
                    AdminPost.categories.contains([query]),
                ]
            )

            search_query = search_query.where(or_(*search_conditions))
            search_query = search_query.order_by(desc(AdminPost.updated_at)).limit(
                limit
            )

            result = await self.session.execute(search_query)
            templates = result.scalars().all()

            logger.info(
                f"Найдено {len(templates)} шаблонов по запросу '{query}' для пользователя {user_id}"
            )
            return list(templates)

        except Exception as e:
            logger.error(f"Ошибка поиска шаблонов: {e}")
            return []

    async def get_recommended_templates(
        self, user_id: int, based_on_categories: list[str], limit: int = 5
    ) -> list[AdminPost]:
        """Получение рекомендованных шаблонов на основе категорий"""
        try:
            if not based_on_categories:
                # Если категории не указаны, возвращаем последние использованные
                return await self.get_user_templates(
                    user_id, limit=limit, sort_by="updated_at", sort_order="desc"
                )

            query = select(AdminPost).where(
                and_(AdminPost.created_by == user_id, AdminPost.is_template)
            )

            # Фильтр по категориям
            category_conditions = [
                AdminPost.categories.contains([category])
                for category in based_on_categories
            ]
            query = query.where(or_(*category_conditions))
            query = query.order_by(desc(AdminPost.updated_at)).limit(limit)

            result = await self.session.execute(query)
            templates = result.scalars().all()

            logger.info(
                f"Найдено {len(templates)} рекомендованных шаблонов для пользователя {user_id}"
            )
            return list(templates)

        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            return []
