import os

from database.db_actions import CaptchaManager
from multicolorcaptcha import CaptchaGenerator


class GenCaptcha:
    def __init__(self) -> None:
        self.GEN_CAPTCHAS_FOLDER = "./captchas"
        os.makedirs(
            self.GEN_CAPTCHAS_FOLDER, exist_ok=True
        )  # Создаем папку для капч, если её нет
        self.captcha_manager = CaptchaManager()

    async def get_captcha(self):
        """
        captcha_size_num -> 0 to 12 by default 2
        difficult_level -> 0 to 6 by default 2
        chars_mode -> "nums", "hex", "ascii" by default "nums"
        multicolor -> True or False by default False
        margin -> True or False by default True
        """
        settings = await self.captcha_manager.get_captcha_settings()
        generator = CaptchaGenerator(settings["captcha_size_number"])
        """
        Use one of the following captcha generation options:
        captcha = generator.gen_captcha_image(multicolor=False, margin=False)
        captcha = generator.gen_captcha_image(multicolor=True, margin=False)
        captcha = generator.gen_captcha_image(multicolor=True, margin=True)
        captcha = generator.gen_captcha_image(difficult_level=1)
        captcha = generator.gen_captcha_image(difficult_level=4)
        captcha = generator.gen_captcha_image(chars_mode="hex")
        captcha = generator.gen_captcha_image(chars_mode="ascii")
        captcha = generator.gen_captcha_image(difficult_level=5, multicolor=True, chars_mode="ascii")
        """
        captcha = generator.gen_captcha_image(
            difficult_level=settings["difficult_level"],
            multicolor=settings["multicolor"],
            chars_mode=settings["chars_mode"],
            margin=settings["margin"],
        )
        image = captcha.image
        characters = captcha.characters

        # Сохраняем изображение капчи во временную директорию
        file_path = os.path.join(self.GEN_CAPTCHAS_FOLDER, "captcha.png")
        image.save(file_path)  # Создаем папку для капчи, если её нет

        return file_path, characters

    async def get_math_captcha(self):
        settings = await self.captcha_manager.get_captcha_settings()
        generator = CaptchaGenerator(settings["captcha_size_number"])
        captcha = generator.gen_math_captcha_image(
            difficult_level=settings["difficult_level"],
            multicolor=settings["multicolor"],
            allow_multiplication=settings["allow_multiplication"],
            margin=settings["margin"],
        )
        image = captcha.image
        equation_str = captcha.equation_str
        equation_result = captcha.equation_result
        file_path = os.path.join(self.GEN_CAPTCHAS_FOLDER, "math_captcha.png")
        image.save(file_path)  # Создаем папку для капчи, если её нет

        return file_path, equation_str, equation_result
