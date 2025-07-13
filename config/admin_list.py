# admin_list.py - загрузка списка администраторов
"""Модуль для загрузки списка администраторов бота.

Этот модуль предоставляет функции для загрузки и управления списком
администраторов бота из различных источников.
"""

import json
import os
from pathlib import Path
from typing import List

from loguru import logger


def load_admin_ids() -> List[int]:
    """Загружает список ID администраторов из файла admin_ids.json.
    
    Возвращает:
        List[int]: Список ID администраторов
        
    Raises:
        FileNotFoundError: Если файл admin_ids.json не найден
        json.JSONDecodeError: Если файл содержит некорректный JSON
    """
    admin_file = Path("admin_ids.json")
    
    if not admin_file.exists():
        logger.warning(f"Файл {admin_file} не найден. Создаю пустой список администраторов.")
        # Создаем пустой файл с примером
        default_admins = {
            "admin_ids": [],
            "_comment": "Добавьте ID администраторов в массив admin_ids"
        }
        with open(admin_file, "w", encoding="utf-8") as f:
            json.dump(default_admins, f, indent=2, ensure_ascii=False)
        return []
    
    try:
        with open(admin_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            admin_ids = data.get("admin_ids", [])
            
        if not isinstance(admin_ids, list):
            logger.error("admin_ids должен быть списком")
            return []
            
        # Проверяем, что все элементы - числа
        valid_ids = []
        for admin_id in admin_ids:
            if isinstance(admin_id, int):
                valid_ids.append(admin_id)
            else:
                try:
                    valid_ids.append(int(admin_id))
                except (ValueError, TypeError):
                    logger.warning(f"Некорректный ID администратора: {admin_id}")
                    
        logger.info(f"Загружено {len(valid_ids)} администраторов")
        return valid_ids
        
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при чтении файла {admin_file}: {e}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при загрузке администраторов: {e}")
        return []


def save_admin_ids(admin_ids: List[int]) -> bool:
    """Сохраняет список ID администраторов в файл.
    
    Args:
        admin_ids: Список ID администраторов
        
    Returns:
        bool: True если сохранение прошло успешно, False в противном случае
    """
    admin_file = Path("admin_ids.json")
    
    try:
        data = {
            "admin_ids": admin_ids,
            "_comment": "Список ID администраторов бота"
        }
        
        with open(admin_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Список администраторов сохранен в {admin_file}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении списка администраторов: {e}")
        return False


def add_admin(admin_id: int) -> bool:
    """Добавляет нового администратора в список.
    
    Args:
        admin_id: ID нового администратора
        
    Returns:
        bool: True если добавление прошло успешно, False в противном случае
    """
    current_admins = load_admin_ids()
    
    if admin_id in current_admins:
        logger.warning(f"Администратор {admin_id} уже в списке")
        return False
        
    current_admins.append(admin_id)
    return save_admin_ids(current_admins)


def remove_admin(admin_id: int) -> bool:
    """Удаляет администратора из списка.
    
    Args:
        admin_id: ID администратора для удаления
        
    Returns:
        bool: True если удаление прошло успешно, False в противном случае
    """
    current_admins = load_admin_ids()
    
    if admin_id not in current_admins:
        logger.warning(f"Администратор {admin_id} не найден в списке")
        return False
        
    current_admins.remove(admin_id)
    return save_admin_ids(current_admins)


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором.
    
    Args:
        user_id: ID пользователя для проверки
        
    Returns:
        bool: True если пользователь является администратором
    """
    admin_ids = load_admin_ids()
    return user_id in admin_ids
