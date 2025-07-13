# examples/poll_service_usage.py
"""
Примеры использования PollService для управления опросами и викторинами
"""

import asyncio
from datetime import datetime, timedelta
from typing import List

from database import get_session
from database.models import PollType
from database.unit_of_work import UnitOfWork


async def create_simple_poll_example():
    """Пример создания простого опроса"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Создаем пост (предполагается, что пост уже существует)
        post_id = 1  # ID существующего поста
        
        # Создаем простой опрос
        poll = await uow.poll_service.create_poll(
            post_id=post_id,
            question="Какой ваш любимый язык программирования?",
            options=[
                "Python",
                "JavaScript",
                "Java",
                "C++",
                "Другой"
            ],
            poll_type=PollType.SINGLE_CHOICE,
            is_anonymous=True,
            allows_multiple_answers=False
        )
        
        print(f"Создан опрос: {poll.question}")
        print(f"ID опроса: {poll.id}")
        
        return poll.id


async def create_quiz_example():
    """Пример создания викторины"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        post_id = 2  # ID существующего поста
        
        # Создаем викторину
        poll = await uow.poll_service.create_poll(
            post_id=post_id,
            question="Какой год считается началом эры Интернета?",
            options=[
                "1969",
                "1983",
                "1991",
                "1995"
            ],
            poll_type=PollType.QUIZ,
            is_anonymous=False,
            correct_option_id=3,  # Будет установлен после создания опций
            explanation="1991 год - год создания первого веб-сайта Тимом Бернерсом-Ли",
            close_date=datetime.now() + timedelta(days=7)
        )
        
        print(f"Создана викторина: {poll.question}")
        print(f"Правильный ответ: {poll.explanation}")
        
        return poll.id


async def create_multiple_choice_poll():
    """Пример создания опроса с множественным выбором"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        post_id = 3
        
        poll = await uow.poll_service.create_poll(
            post_id=post_id,
            question="Какие технологии вы используете в разработке? (можно выбрать несколько)",
            options=[
                "FastAPI",
                "Django",
                "Flask",
                "SQLAlchemy",
                "PostgreSQL",
                "Redis",
                "Docker",
                "Kubernetes"
            ],
            poll_type=PollType.MULTIPLE_CHOICE,
            allows_multiple_answers=True,
            is_anonymous=True
        )
        
        print(f"Создан опрос с множественным выбором: {poll.question}")
        return poll.id


async def voting_examples(poll_id: int):
    """Примеры голосования в опросе"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Пример голосования пользователя 1
        success, message = await uow.poll_service.vote(
            poll_id=poll_id,
            user_id=1,
            option_ids=[1]  # Выбираем первый вариант
        )
        
        print(f"Голосование пользователя 1: {success} - {message}")
        
        # Пример голосования пользователя 2
        success, message = await uow.poll_service.vote(
            poll_id=poll_id,
            user_id=2,
            option_ids=[2]  # Выбираем второй вариант
        )
        
        print(f"Голосование пользователя 2: {success} - {message}")
        
        # Попытка повторного голосования
        success, message = await uow.poll_service.vote(
            poll_id=poll_id,
            user_id=1,
            option_ids=[3]  # Пытаемся изменить голос
        )
        
        print(f"Повторное голосование пользователя 1: {success} - {message}")


async def multiple_choice_voting_example(poll_id: int):
    """Пример голосования в опросе с множественным выбором"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Пользователь выбирает несколько вариантов
        success, message = await uow.poll_service.vote(
            poll_id=poll_id,
            user_id=3,
            option_ids=[1, 4, 5, 7]  # FastAPI, SQLAlchemy, PostgreSQL, Docker
        )
        
        print(f"Множественное голосование: {success} - {message}")
        
        # Другой пользователь
        success, message = await uow.poll_service.vote(
            poll_id=poll_id,
            user_id=4,
            option_ids=[2, 3, 6]  # Django, Flask, Redis
        )
        
        print(f"Голосование пользователя 4: {success} - {message}")


async def get_poll_results_example(poll_id: int):
    """Пример получения результатов опроса"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        results = await uow.poll_service.get_poll_results(poll_id)
        
        if results:
            print(f"\nРезультаты опроса: {results['question']}")
            print(f"Всего голосов: {results['total_votes']}")
            print(f"Статус: {'Закрыт' if results['is_closed'] else 'Активен'}")
            
            print("\nВарианты ответов:")
            for option in results['options']:
                print(f"  {option['text']}: {option['votes']} голосов ({option['percentage']:.1f}%)")
                if option['is_correct']:
                    print("    ✓ Правильный ответ")
        else:
            print("Опрос не найден")


async def get_quiz_results_example(poll_id: int):
    """Пример получения результатов викторины"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        results = await uow.poll_service.get_quiz_results(poll_id)
        
        if results and results.get('quiz_stats'):
            quiz_stats = results['quiz_stats']
            print(f"\nСтатистика викторины: {results['question']}")
            print(f"Правильных ответов: {quiz_stats['correct_answers']}")
            print(f"Неправильных ответов: {quiz_stats['incorrect_answers']}")
            print(f"Процент правильных ответов: {quiz_stats['correct_percentage']:.1f}%")
            print(f"Уровень сложности: {quiz_stats['difficulty_level']}")
            
            if results.get('explanation'):
                print(f"Объяснение: {results['explanation']}")
        else:
            print("Это не викторина или викторина не найдена")


async def get_user_quiz_score_example(user_id: int):
    """Пример получения статистики пользователя по викторинам"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        score = await uow.poll_service.get_user_quiz_score(user_id)
        
        print(f"\nСтатистика пользователя {user_id} по викторинам:")
        print(f"Всего викторин: {score['total_quizzes']}")
        print(f"Правильных ответов: {score['correct_answers']}")
        print(f"Точность: {score['accuracy_percentage']:.1f}%")


async def poll_management_examples():
    """Примеры управления опросами"""
    async with get_session() as session:
        uow = UnitOfWork(session)
        
        # Получение активных опросов
        active_polls = await uow.poll_service.get_active_polls(limit=10)
        print(f"\nАктивных опросов: {len(active_polls)}")
        
        # Получение опросов по типу
        quizzes = await uow.poll_service.get_polls_by_type(PollType.QUIZ, limit=5)
        print(f"Викторин: {len(quizzes)}")
        
        # Закрытие истекших опросов
        closed_count = await uow.poll_service.close_expired_polls()
        print(f"Закрыто истекших опросов: {closed_count}")
        
        # Очистка старых голосов
        cleaned_votes = await uow.poll_service.cleanup_old_votes(days=30)
        print(f"Очищено старых голосов: {cleaned_votes}")


async def telegram_bot_integration_example():
    """Пример интеграции с Telegram ботом"""
    
    # Пример обработчика команды создания опроса
    async def create_poll_command(message, bot):
        """Обработчик команды /create_poll"""
        async with get_session() as session:
            uow = UnitOfWork(session)
            
            # Создаем пост для опроса
            post = await uow.admin_post_service.create_draft(
                title="Новый опрос",
                content="Участвуйте в нашем опросе!",
                author_id=message.from_user.id
            )
            
            # Создаем опрос
            poll = await uow.poll_service.create_poll(
                post_id=post.id,
                question="Как вам наш бот?",
                options=["Отлично", "Хорошо", "Нормально", "Плохо"],
                poll_type=PollType.SINGLE_CHOICE,
                is_anonymous=True
            )
            
            # Отправляем опрос в Telegram
            await bot.send_poll(
                chat_id=message.chat.id,
                question=poll.question,
                options=[opt.text for opt in poll.options],
                is_anonymous=poll.is_anonymous
            )
    
    # Пример обработчика голосования
    async def poll_answer_handler(poll_answer, bot):
        """Обработчик ответов на опрос"""
        async with get_session() as session:
            uow = UnitOfWork(session)
            
            # Находим опрос по ID (нужно сохранять соответствие)
            poll_id = 1  # Получаем из базы по poll_answer.poll_id
            
            # Регистрируем голос
            success, message = await uow.poll_service.vote(
                poll_id=poll_id,
                user_id=poll_answer.user.id,
                option_ids=[poll_answer.option_ids[0]]  # Первый выбранный вариант
            )
            
            if success:
                # Получаем обновленные результаты
                results = await uow.poll_service.get_poll_results(poll_id)
                
                # Отправляем результаты (если опрос не анонимный)
                if not results['is_anonymous']:
                    result_text = f"Результаты опроса:\n"
                    for option in results['options']:
                        result_text += f"{option['text']}: {option['votes']} ({option['percentage']:.1f}%)\n"
                    
                    await bot.send_message(
                        chat_id=poll_answer.user.id,
                        text=result_text
                    )
    
    print("Примеры интеграции с Telegram ботом созданы")


async def main():
    """Главная функция с примерами использования"""
    print("=== Примеры использования PollService ===")
    
    # Создание опросов
    print("\n1. Создание простого опроса")
    simple_poll_id = await create_simple_poll_example()
    
    print("\n2. Создание викторины")
    quiz_poll_id = await create_quiz_example()
    
    print("\n3. Создание опроса с множественным выбором")
    multiple_poll_id = await create_multiple_choice_poll()
    
    # Голосование
    print("\n4. Примеры голосования")
    await voting_examples(simple_poll_id)
    
    print("\n5. Голосование с множественным выбором")
    await multiple_choice_voting_example(multiple_poll_id)
    
    # Результаты
    print("\n6. Получение результатов опроса")
    await get_poll_results_example(simple_poll_id)
    
    print("\n7. Получение результатов викторины")
    await get_quiz_results_example(quiz_poll_id)
    
    print("\n8. Статистика пользователя по викторинам")
    await get_user_quiz_score_example(1)
    
    # Управление
    print("\n9. Управление опросами")
    await poll_management_examples()
    
    print("\n10. Интеграция с Telegram ботом")
    await telegram_bot_integration_example()
    
    print("\n=== Примеры завершены ===")


if __name__ == "__main__":
    asyncio.run(main())