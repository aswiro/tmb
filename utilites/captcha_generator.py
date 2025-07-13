from pathlib import Path

from database.models.captcha_setting import CaptchaSetting
from loguru import logger
from multicolorcaptcha import CaptchaGenerator


class CaptchaGenerators:
    def __init__(self, captcha_settings: CaptchaSetting):
        self.captcha_settings = captcha_settings
        self.captcha_path = Path(__file__).parent / "captcha"
        self.captcha_path.mkdir(exist_ok=True)

    async def get_captcha(self, answer: bool = False) -> str:
        """Генерация каптчи в зависимости от настроек и возврат пути к файлу.
        captcha_size_num -> 0 to 12 by default 2
        difficult_level -> 0 to 6 by default 2
        chars_mode -> "nums", "hex", "ascii" by default "nums"
        multicolor -> True or False by default False
        margin -> True or False by default True

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

        generator = CaptchaGenerator(int(self.captcha_settings.captcha_size))

        captcha_type = self.captcha_settings.captcha_type
        file_path = self.captcha_path / f"{captcha_type}_captcha.png"

        if captcha_type == "standard":
            captcha = generator.gen_captcha_image(
                difficult_level=self.captcha_settings.difficult_level,
                multicolor=self.captcha_settings.multicolor,
                chars_mode=self.captcha_settings.chars_mode,
                margin=self.captcha_settings.margin,
            )
            image = captcha.image
            characters = captcha.characters
            logger.debug(f"Generated standard captcha. Characters: {characters}")
            image.save(file_path, "png")
        elif captcha_type == "math":
            math_captcha = generator.gen_math_captcha_image(
                difficult_level=self.captcha_settings.difficult_level,
                multicolor=self.captcha_settings.multicolor,
                allow_multiplication=self.captcha_settings.allow_multiplication,
                margin=self.captcha_settings.margin,
            )
            image = math_captcha.image
            equation_str = math_captcha.equation_str
            equation_result = math_captcha.equation_result
            logger.debug(
                f"Generated math captcha. Equation: {equation_str}, Result: {equation_result}"
            )
            image.save(file_path, "png")
        else:
            logger.error(f"Unknown captcha type:\n{captcha_type}")
            return ""  # Or raise an error

        logger.debug(f"Captcha image saved to:\n{file_path}")
        if answer:
            return {
                "path": str(file_path),
                "equation": equation_str,
                "result": equation_result,
            }
        return str(file_path)
