{{ date }}, в [подписку]({{ url }}) PlayStation Plus {{ tier }} и выше, будут добавлены:

{% for game in games %}
• {{ game }}
{% endfor %}
{% if premium_games %}

В каталог PlayStation Plus Premium добавят:
{% for game in premium_games %}
• {{ game }}
{% endfor %}
{% endif %}
#покаинтересно@brknbtns #игры@brknbtns
