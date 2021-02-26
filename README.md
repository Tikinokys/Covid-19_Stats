# Covid-19_Stats

Telegram-бот отображающий статистику по Covid-19 в виде графов.

База данных взята с https://github.com/CSSEGISandData/COVID-19 преобразованная с помощью https://github.com/pomber/covid19

Telegram-бот размещен на платформе [Heroku](https://www.heroku.com/)


Информация об эксплуатации (готового Telegram-бота)
---------
Имя Telegram-бота:
```
Covid-19_Stats
```
Команды:
```
/start - Начало работы с Telegram-ботом. Выводит приветственное сообщение с доступными командами.
/country - Предоставляет список стран. Выберите любую, чтобы получать статистику по Covid-19 выбранной страны.
/stats - Открывает клавиатуру с опциями предоставления информации по Covid-19.
```


Начало работы (Запуск своего Telegram-бота)
---------
1) Зарегистируйте своего бота Telegram с помощью @BotFather

2) Разместите вашего Telegram-бота на любой подходящей облачной платформе

3) Создайте файл *.prefs* и укажите в нем свои конфигурационные данные
```
token_prod=????? // токен вашего Telegram-бота (для релиза)
token_debug=????? // токен вашего Telegram-бота (для отладки)
webhook_url=????? // адрес вашего хранилища Telegram-бота на облачной платформе
```
4) Установите requirements.txt
```
$ pip install -r requirements.txt
```
5) Установите виртуальную среду
```
$ pip install virtualenv
$ virtualenv my_env
$ cd my_env/Scripts
$ activate.bat
```
6) Запустите локально для установки конфигурационных данных (в корневой папке где лежит main.py)
```
$ Python main.py
```


Github
---------
https://github.com/Tikinokys/Covid-19_Stats