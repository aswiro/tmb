# database/services/poll_service.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Poll, PollOption, PollType, PollVote, AdminPost, User
from ..repository import Repository


class PollService:
    """Сервис для управления опросами и викторинами"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.poll_repo = Repository(session, Poll)
        self.option_repo = Repository(session, PollOption)
        self.vote_repo = Repository(session, PollVote)

    # Создание и управление опросами
    async def create_poll(
        self,
        post_id: int,
        question: str,
        options: List[str],
        poll_type: PollType = PollType.SINGLE_CHOICE,
        is_anonymous: bool = True,
        allows_multiple_answers: bool = False,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
        open_period: Optional[int] = None,
        close_date: Optional[datetime] = None,
    ) -> Poll:
        """Создание нового опроса"""
        # Создаем опрос
        poll_data = {
            "post_id": post_id,
            "question": question,
            "poll_type": poll_type,
            "is_anonymous": is_anonymous,
            "allows_multiple_answers": allows_multiple_answers,
            "correct_option_id": correct_option_id,
            "explanation": explanation,
            "open_period": open_period,
            "close_date": close_date,
        }
        
        poll = await self.poll_repo.create(**poll_data)
        
        # Создаем варианты ответов
        for position, option_text in enumerate(options):
            await self.option_repo.create(
                poll_id=poll.id,
                text=option_text,
                position=position
            )
        
        return poll

    async def update_poll(
        self,
        poll_id: int,
        question: Optional[str] = None,
        options: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[Poll]:
        """Обновление опроса"""
        poll = await self.get_poll_by_id(poll_id)
        if not poll or poll.is_closed:
            return None
        
        # Обновляем основные данные опроса
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if question:
            update_data["question"] = question
        
        if update_data:
            poll = await self.poll_repo.update(poll, **update_data)
        
        # Обновляем варианты ответов если переданы
        if options is not None:
            # Удаляем старые варианты
            await self.option_repo.delete_by_condition(PollOption.poll_id == poll_id)
            
            # Создаем новые варианты
            for position, option_text in enumerate(options):
                await self.option_repo.create(
                    poll_id=poll.id,
                    text=option_text,
                    position=position
                )
        
        return poll

    async def delete_poll(self, poll_id: int) -> bool:
        """Удаление опроса"""
        poll = await self.get_poll_by_id(poll_id)
        if not poll:
            return False
        
        await self.poll_repo.delete(poll)
        return True

    async def close_poll(self, poll_id: int) -> Optional[Poll]:
        """Закрытие опроса"""
        poll = await self.get_poll_by_id(poll_id)
        if not poll:
            return None
        
        return await self.poll_repo.update(poll, is_closed=True)

    # Получение опросов
    async def get_poll_by_id(self, poll_id: int) -> Optional[Poll]:
        """Получение опроса по ID"""
        return await self.poll_repo.get_by_id(
            poll_id,
            options=[
                selectinload(Poll.options),
                selectinload(Poll.votes),
                selectinload(Poll.post)
            ]
        )

    async def get_poll_by_post_id(self, post_id: int) -> Optional[Poll]:
        """Получение опроса по ID поста"""
        return await self.poll_repo.get_by_condition(
            Poll.post_id == post_id,
            options=[
                selectinload(Poll.options),
                selectinload(Poll.votes)
            ]
        )

    async def get_active_polls(self, limit: int = 50) -> List[Poll]:
        """Получение активных опросов"""
        return await self.poll_repo.get_all(
            conditions=[Poll.is_closed == False],
            order_by=[desc(Poll.created_at)],
            limit=limit,
            options=[selectinload(Poll.options)]
        )

    async def get_polls_by_type(self, poll_type: PollType, limit: int = 50) -> List[Poll]:
        """Получение опросов по типу"""
        return await self.poll_repo.get_all(
            conditions=[Poll.poll_type == poll_type],
            order_by=[desc(Poll.created_at)],
            limit=limit,
            options=[selectinload(Poll.options)]
        )

    async def get_expired_polls(self) -> List[Poll]:
        """Получение истекших опросов"""
        now = datetime.now()
        return await self.poll_repo.get_all(
            conditions=[
                Poll.is_closed == False,
                Poll.close_date <= now
            ],
            options=[selectinload(Poll.options)]
        )

    # Голосование
    async def vote(
        self,
        poll_id: int,
        user_id: int,
        option_ids: List[int]
    ) -> Tuple[bool, str]:
        """Голосование в опросе
        
        Returns:
            Tuple[bool, str]: (успех, сообщение об ошибке)
        """
        poll = await self.get_poll_by_id(poll_id)
        if not poll:
            return False, "Опрос не найден"
        
        if poll.is_closed:
            return False, "Опрос закрыт"
        
        # Проверяем срок действия опроса
        if poll.close_date and poll.close_date <= datetime.now():
            await self.close_poll(poll_id)
            return False, "Срок опроса истек"
        
        # Проверяем, голосовал ли пользователь ранее
        existing_vote = await self.vote_repo.get_by_condition(
            and_(PollVote.poll_id == poll_id, PollVote.user_id == user_id)
        )
        
        if existing_vote and not poll.allows_multiple_answers:
            return False, "Вы уже голосовали в этом опросе"
        
        # Проверяем количество выбранных вариантов
        if not poll.allows_multiple_answers and len(option_ids) > 1:
            return False, "Можно выбрать только один вариант"
        
        # Проверяем существование вариантов
        valid_options = await self.option_repo.get_all(
            conditions=[
                PollOption.poll_id == poll_id,
                PollOption.id.in_(option_ids)
            ]
        )
        
        if len(valid_options) != len(option_ids):
            return False, "Некорректные варианты ответов"
        
        # Удаляем предыдущие голоса если разрешено переголосование
        if existing_vote and poll.allows_multiple_answers:
            await self.vote_repo.delete_by_condition(
                and_(PollVote.poll_id == poll_id, PollVote.user_id == user_id)
            )
        
        # Создаем новые голоса
        for option_id in option_ids:
            await self.vote_repo.create(
                poll_id=poll_id,
                option_id=option_id,
                user_id=user_id
            )
        
        # Обновляем счетчики
        await self._update_vote_counts(poll_id)
        
        return True, "Голос учтен"

    async def remove_vote(self, poll_id: int, user_id: int) -> bool:
        """Удаление голоса пользователя"""
        poll = await self.get_poll_by_id(poll_id)
        if not poll or poll.is_closed:
            return False
        
        deleted_count = await self.vote_repo.delete_by_condition(
            and_(PollVote.poll_id == poll_id, PollVote.user_id == user_id)
        )
        
        if deleted_count > 0:
            await self._update_vote_counts(poll_id)
            return True
        
        return False

    async def get_user_vote(self, poll_id: int, user_id: int) -> Optional[List[PollVote]]:
        """Получение голосов пользователя в опросе"""
        return await self.vote_repo.get_all(
            conditions=[
                PollVote.poll_id == poll_id,
                PollVote.user_id == user_id
            ],
            options=[selectinload(PollVote.option)]
        )

    # Результаты и статистика
    async def get_poll_results(self, poll_id: int) -> Optional[Dict]:
        """Получение результатов опроса"""
        poll = await self.get_poll_by_id(poll_id)
        if not poll:
            return None
        
        results = {
            "poll_id": poll.id,
            "question": poll.question,
            "poll_type": poll.poll_type.value,
            "total_votes": poll.total_voter_count,
            "is_closed": poll.is_closed,
            "is_quiz": poll.is_quiz,
            "correct_option_id": poll.correct_option_id,
            "explanation": poll.explanation,
            "options": []
        }
        
        for option in poll.options:
            option_data = {
                "id": option.id,
                "text": option.text,
                "votes": option.voter_count,
                "percentage": option.percentage,
                "is_correct": option.id == poll.correct_option_id
            }
            results["options"].append(option_data)
        
        return results

    async def get_poll_statistics(self, poll_id: int) -> Optional[Dict]:
        """Получение детальной статистики опроса"""
        poll = await self.get_poll_by_id(poll_id)
        if not poll:
            return None
        
        # Базовая статистика
        stats = await self.get_poll_results(poll_id)
        
        # Дополнительная статистика
        vote_times = await self.session.execute(
            func.extract('hour', PollVote.voted_at).label('hour'),
            func.count(PollVote.id).label('count')
        ).where(PollVote.poll_id == poll_id).group_by('hour')
        
        stats["vote_distribution_by_hour"] = dict(vote_times.fetchall())
        
        # Статистика по дням
        vote_days = await self.session.execute(
            func.date(PollVote.voted_at).label('date'),
            func.count(PollVote.id).label('count')
        ).where(PollVote.poll_id == poll_id).group_by('date')
        
        stats["vote_distribution_by_day"] = dict(vote_days.fetchall())
        
        return stats

    async def get_quiz_results(self, poll_id: int) -> Optional[Dict]:
        """Получение результатов викторины"""
        poll = await self.get_poll_by_id(poll_id)
        if not poll or not poll.is_quiz:
            return None
        
        results = await self.get_poll_results(poll_id)
        
        # Подсчет правильных и неправильных ответов
        correct_votes = await self.vote_repo.count(
            conditions=[
                PollVote.poll_id == poll_id,
                PollVote.option_id == poll.correct_option_id
            ]
        )
        
        total_votes = poll.total_voter_count
        incorrect_votes = total_votes - correct_votes
        
        results["quiz_stats"] = {
            "correct_answers": correct_votes,
            "incorrect_answers": incorrect_votes,
            "correct_percentage": (correct_votes / total_votes * 100) if total_votes > 0 else 0,
            "difficulty_level": self._calculate_difficulty(correct_votes, total_votes)
        }
        
        return results

    async def get_user_quiz_score(self, user_id: int, limit: int = 10) -> Dict:
        """Получение статистики пользователя по викторинам"""
        # Получаем все голоса пользователя в викторинах
        quiz_votes = await self.session.execute(
            PollVote.poll_id,
            PollVote.option_id,
            Poll.correct_option_id
        ).select_from(
            PollVote.join(Poll)
        ).where(
            and_(
                PollVote.user_id == user_id,
                Poll.correct_option_id.isnot(None)
            )
        ).order_by(desc(PollVote.voted_at)).limit(limit)
        
        votes = quiz_votes.fetchall()
        
        total_quizzes = len(votes)
        correct_answers = sum(1 for vote in votes if vote.option_id == vote.correct_option_id)
        
        return {
            "user_id": user_id,
            "total_quizzes": total_quizzes,
            "correct_answers": correct_answers,
            "accuracy_percentage": (correct_answers / total_quizzes * 100) if total_quizzes > 0 else 0,
            "recent_quizzes": votes
        }

    # Служебные методы
    async def _update_vote_counts(self, poll_id: int) -> None:
        """Обновление счетчиков голосов"""
        # Обновляем счетчики для каждой опции
        options = await self.option_repo.get_all(
            conditions=[PollOption.poll_id == poll_id]
        )
        
        for option in options:
            vote_count = await self.vote_repo.count(
                conditions=[PollVote.option_id == option.id]
            )
            await self.option_repo.update(option, voter_count=vote_count)
        
        # Обновляем общий счетчик опроса
        total_voters = await self.session.execute(
            func.count(func.distinct(PollVote.user_id))
        ).where(PollVote.poll_id == poll_id).scalar()
        
        poll = await self.poll_repo.get_by_id(poll_id)
        if poll:
            await self.poll_repo.update(poll, total_voter_count=total_voters)

    def _calculate_difficulty(self, correct_answers: int, total_answers: int) -> str:
        """Расчет уровня сложности викторины"""
        if total_answers == 0:
            return "unknown"
        
        percentage = correct_answers / total_answers * 100
        
        if percentage >= 80:
            return "easy"
        elif percentage >= 50:
            return "medium"
        elif percentage >= 20:
            return "hard"
        else:
            return "very_hard"

    # Автоматические задачи
    async def close_expired_polls(self) -> int:
        """Закрытие истекших опросов"""
        expired_polls = await self.get_expired_polls()
        closed_count = 0
        
        for poll in expired_polls:
            await self.close_poll(poll.id)
            closed_count += 1
        
        return closed_count

    async def cleanup_old_votes(self, days: int = 90) -> int:
        """Очистка старых голосов (для анонимных опросов)"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Удаляем голоса в анонимных опросах старше указанного периода
        deleted_count = await self.vote_repo.delete_by_condition(
            and_(
                PollVote.voted_at < cutoff_date,
                PollVote.poll_id.in_(
                    self.session.query(Poll.id).filter(Poll.is_anonymous == True)
                )
            )
        )
        
        return deleted_count